"""Apply targeted repairs to legacy questions in the restored clone.

The repair deliberately updates the live canonical row in place instead of
calling ``replace_question``: the service would clone any question with
attempt history, leaving the defective original in service. Historical
attempts keep their frozen ``question_snapshot``; only the current bank row
and its current Vietnamese translation change. Every repaired row is then
revalidated by the production validator.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import text

from app.benchmark import ROOT_DIR
from app.config import get_settings
from app.db import get_session_factory
from app.repositories import QuestionRepository
from app.services import question_service as questions
from app.services.question_localization import (
    source_fingerprint,
    translation_is_current,
)
from app.services.sandbox_runner import SandboxRunner


def _load_repairs(path: Path) -> dict:
    spec_dir = str(path.parent.resolve())
    if spec_dir not in sys.path:
        sys.path.insert(0, spec_dir)
    spec = importlib.util.spec_from_file_location("expansion_repairs", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.REPAIRS


def _require_clone(settings) -> None:
    parts = urlsplit(settings.database_url)
    if (parts.path or "").lstrip("/") != "dbcas_clone":
        raise SystemExit("Refusing to repair outside the restored clone 'dbcas_clone'")


def main() -> int:
    settings = get_settings()
    _require_clone(settings)
    repairs = _load_repairs(
        ROOT_DIR / "_content/expansion-20261024/specs/repairs.py"
    )
    runner = SandboxRunner(settings)
    db = get_session_factory()()
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "target": "dbcas_clone",
        "questions": [],
        "candidate": None,
    }
    try:
        repo = QuestionRepository(db)
        for question_id, repair in sorted(repairs.items()):
            question = repo.get_detail(question_id)
            if question is None:
                report["questions"].append(
                    {"question_id": question_id, "status": "not_found"}
                )
                continue
            if question.status == "retired":
                report["questions"].append(
                    {
                        "question_id": question_id,
                        "before": {"status": "retired"},
                        "after": {"status": "retired", "modified": False},
                        "validation": "skipped_retired_unmodified",
                    }
                )
                print(f"[skipped_retired] question {question_id}")
                continue
            before = {
                "status": question.status,
                "explanation": question.explanation,
                "tags": list(question.tags or []),
                "source_refs": list(question.source_refs or []),
                "reference_answer": question.reference_answer,
                "translation_current": {
                    row.locale: translation_is_current(question, row)
                    for row in question.translations
                },
            }
            question.explanation = repair["explanation_en"]
            question.tags = list(repair["tags"])
            question.source_refs = [
                ref.model_dump() if hasattr(ref, "model_dump") else ref
                for ref in repair["source_refs"]
            ]
            if repair.get("reference_answer"):
                question.reference_answer = repair["reference_answer"]
            question.updated_at = datetime.now(timezone.utc)
            db.flush()

            translation_rows = []
            for row in question.translations:
                if row.locale != "vi":
                    continue
                translation_rows.append(
                    {
                        "locale": "vi",
                        "prompt": row.prompt,
                        "explanation": repair["explanation_vi"],
                        "option_texts": row.option_texts or {},
                        "rubrics": row.rubrics or {},
                    }
                )
            if translation_rows:
                questions.upsert_question_translations(
                    db, question, translation_rows
                )
            db.commit()

            validation = "skipped_retired"
            if question.status == "validated":
                try:
                    questions.set_question_status(
                        db, question_id, "validated", runner
                    )
                    validation = "validated"
                except Exception as exc:  # noqa: BLE001
                    validation = f"failed: {getattr(exc, 'message', exc)}"

            refreshed = repo.get_detail(question_id)
            after = {
                "status": refreshed.status,
                "explanation_sha256": hashlib.sha256(
                    (refreshed.explanation or "").encode("utf-8")
                ).hexdigest(),
                "tags": list(refreshed.tags or []),
                "source_ref_count": len(refreshed.source_refs or []),
                "reference_answer_present": bool(refreshed.reference_answer),
                "translation_current": {
                    row.locale: translation_is_current(refreshed, row)
                    for row in refreshed.translations
                },
                "source_fingerprint": source_fingerprint(refreshed),
            }
            report["questions"].append(
                {
                    "question_id": question_id,
                    "before": before,
                    "after": after,
                    "validation": validation,
                }
            )
            print(f"[{validation}] question {question_id}")

        candidate = db.execute(
            text("select candidate_id, validation_detail from question_candidate where candidate_id = 1")
        ).fetchone()
        if candidate:
            detail = dict(candidate[1] or {})
            detail["decision"] = "rejected_not_promoted"
            detail["reason"] = (
                "Duplicate knowledge point: question 211 already assesses "
                "SELECT ... FOR UPDATE at the same PG-LOCK EASY band."
            )
            detail["duplicate_of_question_id"] = 211
            db.execute(
                text(
                    "update question_candidate set validation_status = 'rejected', "
                    "validation_detail = cast(:detail as jsonb) where candidate_id = 1"
                ),
                {"detail": json.dumps(detail, ensure_ascii=False)},
            )
            db.commit()
            report["candidate"] = {
                "candidate_id": 1,
                "decision": "rejected_not_promoted",
                "duplicate_of_question_id": 211,
            }
            print("[rejected] candidate 1 (duplicate of question 211)")
    finally:
        db.close()

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    out = ROOT_DIR / "_content/expansion-20261024/evidence/repairs_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out}")
    return 0 if all(
        item.get("validation") in {"validated", "skipped_retired", "skipped_retired_unmodified"}
        for item in report["questions"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
