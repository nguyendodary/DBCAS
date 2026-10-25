"""Reconcile staged clone questions with the reviewed specs.

Content review found five defects across the 271 staged questions:

* Q574 proposed ON CONFLICT ON CONSTRAINT for a unique *expression* index,
  which PostgreSQL cannot accept (an expression index is not a constraint).
* Q594 described websearch_to_tsquery negation as if it applied to the whole
  OR expression, although AND binds more tightly than OR.
* Q625's explanation said two payments where the fixture has three.
* Q573 stated an absolute RETURNING rule that changed in PostgreSQL 18, so it
  is now scoped to PostgreSQL 17.
* The authored bank placed the correct option at A in 166 of 199 MCQs. Every
  MCQ is now moved to a deterministic position derived from its key.

Only questions recorded in ``staging_manifest.json`` are touched. The script
refuses any database other than ``dbcas_clone`` and revalidates every changed
question through the production service. Vietnamese drafts are rotated by the
same label permutation; they remain pending human review and are not imported.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import text

from app.benchmark import ROOT_DIR
from app.config import get_settings
from app.db import get_session_factory
from app.repositories import CurriculumRepository, QuestionRepository
from app.services import question_service as questions
from app.services.sandbox_runner import SandboxRunner

EXPANSION = ROOT_DIR / "_content/expansion-20261024"
SPEC_DIR = EXPANSION / "specs"
MANIFEST = EXPANSION / "generated/staging_manifest.json"
PENDING = EXPANSION / "generated/translations_vi_pending.json"
EVIDENCE = EXPANSION / "evidence/review_repairs.json"

SKIP_SPECS = {"lib", "gap_lib", "sources", "repairs", "__init__"}


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_all_specs() -> tuple[dict[str, dict], dict[str, str]]:
    if str(SPEC_DIR) not in sys.path:
        sys.path.insert(0, str(SPEC_DIR))
    lib = _load_module(SPEC_DIR / "lib.py", "review_lib")
    items: dict[str, dict] = {}
    files: dict[str, str] = {}
    for path in sorted(SPEC_DIR.glob("*.py")):
        if path.stem in SKIP_SPECS:
            continue
        module = _load_module(path, f"review_spec_{path.stem}")
        batch = getattr(module, "QUESTIONS", None)
        if not isinstance(batch, list):
            continue
        for item in lib.normalize_items(batch):
            key = item["key"]
            if key in items:
                raise SystemExit(f"Duplicate spec key {key} in {path.name}")
            items[key] = item
            files[key] = path.name
    return items, files


def _option_signature(question) -> list[tuple[str, str, bool]]:
    return sorted(
        (option.option_label, option.option_text, bool(option.is_correct))
        for option in question.options
    )


def _item_option_signature(item: dict) -> list[tuple[str, str, bool]]:
    return sorted(
        (option["option_label"], option["option_text"], bool(option["is_correct"]))
        for option in item["options"]
    )


def _correct_label(options) -> str:
    labels = [label for label, _, correct in options if correct]
    return labels[0] if labels else "?"


def _require_clone(settings) -> None:
    parts = urlsplit(settings.database_url)
    if (parts.path or "").lstrip("/") != "dbcas_clone":
        raise SystemExit("Refusing to repair outside the restored clone 'dbcas_clone'")


def main() -> int:
    settings = get_settings()
    _require_clone(settings)
    from build import _build_payload, _compute_expected  # noqa: WPS433 - script import

    items, files = _load_all_specs()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["questions"]
    if set(items) != set(manifest):
        raise SystemExit(
            "Spec keys and staging manifest differ: "
            f"missing={sorted(set(manifest) - set(items))[:5]} "
            f"extra={sorted(set(items) - set(manifest))[:5]}"
        )

    runner = SandboxRunner(settings)
    db = get_session_factory()()
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "target": "dbcas_clone",
        "spec_files": dict(sorted(Counter(files.values()).items())),
        "questions_in_specs": len(items),
        "questions_in_manifest": len(manifest),
        "changes": [],
        "validated": 0,
        "failed": [],
        "vi_drafts_rotated": 0,
        "vi_drafts_unchanged": 0,
    }
    try:
        concepts = {            concept.concept_code: concept
            for concept in CurriculumRepository(db).list_concepts()
        }
        concept_ids = {code: concept.concept_id for code, concept in concepts.items()}
        repo = QuestionRepository(db)

        before_labels = Counter(
            label
            for (label,) in db.execute(
                text(
                    "select o.option_label from mcq_option o "
                    "join question q on q.question_id = o.question_id "
                    "where o.is_correct and q.question_id between 451 and 721"
                )
            )
        )

        # 1. Content/order repairs for MCQs and the one corrected SQL item.
        for key, item in sorted(items.items()):
            qid = manifest[key]["question_id"]
            question = repo.get_detail(qid)
            if question is None:
                raise SystemExit(f"Question {qid} for {key} is missing from the clone")
            fields = []
            if question.prompt != item["prompt"]:
                fields.append("prompt")
            if (question.explanation or "") != (item.get("explanation") or ""):
                fields.append("explanation")
            if item["question_type"] == "mcq":
                if _option_signature(question) != _item_option_signature(item):
                    fields.append("options")
            elif item["question_type"] == "sql":
                if (question.reference_answer or "") != item["reference_answer"]:
                    fields.append("reference_answer")
            if not fields:
                continue

            datasets = []
            if item["question_type"] == "sql":
                ordered = bool(item.get("ordered", True))
                check_columns = bool(item.get("check_columns", True))
                for dataset in item["datasets"]:
                    expected = _compute_expected(
                        runner, dataset, item["reference_answer"], ordered, check_columns
                    )
                    datasets.append(
                        {
                            "dataset_name": dataset["dataset_name"],
                            "setup_sql": dataset["setup_sql"],
                            "expected_result": expected,
                            "is_edge_case": bool(dataset.get("is_edge_case")),
                        }
                    )

            payload = _build_payload(item, concept_ids, datasets)
            before_correct = (
                _correct_label(_option_signature(question))
                if item["question_type"] == "mcq"
                else None
            )
            after_correct = (
                _correct_label(_item_option_signature(item))
                if item["question_type"] == "mcq"
                else None
            )
            try:
                questions.replace_question(db, qid, payload)
                questions.set_question_status(db, qid, "validated", runner)
                status = "validated"
            except Exception as exc:  # noqa: BLE001 - record and continue safely
                status = f"failed: {getattr(exc, 'message', exc)}"
                report["failed"].append({"question_id": qid, "key": key, "error": status})
            report["changes"].append(
                {
                    "question_id": qid,
                    "key": key,
                    "question_type": item["question_type"],
                    "fields": fields,
                    "correct_label_before": before_correct,
                    "correct_label_after": after_correct,
                    "validation": status,
                }
            )
            print(f"[{status}] {qid} {key} ({', '.join(fields)})")

        # 2. Rotate pending Vietnamese option mappings by the same permutation.
        # The marker keeps reruns idempotent: drafts are rotated exactly once.
        pending = json.loads(PENDING.read_text(encoding="utf-8"))
        if pending.get("option_normalization") is None:
            for key, draft in pending["questions"].items():
                item = items.get(key)
                if item is None or item["question_type"] != "mcq" or not draft.get("option_texts"):
                    report["vi_drafts_unchanged"] += 1
                    continue
                permutation = item.get("_rotation") or list(
                    range(len(item.get("options") or []))
                )
                source = draft["option_texts"]
                draft["option_texts"] = {
                    "ABCD"[new_index]: source[old_label]
                    for old_label, new_index in zip("ABCD", permutation)
                    if old_label in source
                }
                report["vi_drafts_rotated"] += 1
            pending["option_normalization"] = "2026-10-25-key-hash"
        else:
            report["vi_drafts_unchanged"] = len(pending["questions"])
        pending["review_status"] = "pending_human_review"
        pending["imported"] = False
        PENDING.write_text(
            json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        report["validated"] = sum(
            1 for change in report["changes"] if change["validation"] == "validated"
        )
        after_labels = Counter(
            label
            for (label,) in db.execute(
                __import__("sqlalchemy").text(
                    "select o.option_label from mcq_option o "
                    "join question q on q.question_id = o.question_id "
                    "where o.is_correct and q.question_id between 451 and 721"
                )
            )
        )
        report["answer_positions"] = {
            "before": dict(sorted(before_labels.items())),
            "after": dict(sorted(after_labels.items())),
        }
        report["all_staged_validated"] = db.execute(
            __import__("sqlalchemy").text(
                "select count(*) from question where question_id between 451 and 721 "
                "and status = 'validated'"
            )
        ).scalar_one()
    finally:
        db.close()

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "changed": len(report["changes"]),
                "validated": report["validated"],
                "failed": len(report["failed"]),
                "answer_positions": report["answer_positions"],
                "all_staged_validated": report["all_staged_validated"],
                "vi_drafts_rotated": report["vi_drafts_rotated"],
            },
            indent=2,
        )
    )
    print(f"Wrote {EVIDENCE}")
    return 0 if not report["failed"] and report["all_staged_validated"] == 271 else 1


if __name__ == "__main__":
    raise SystemExit(main())
