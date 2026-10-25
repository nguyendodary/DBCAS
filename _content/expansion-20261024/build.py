"""Stage expansion questions into the restored clone through the real services.

Safety properties:
* refuses to run against any database other than ``dbcas_clone``;
* creates questions through ``question_service.create_question`` and validates
  them through ``question_service.set_question_status``;
* derives every SQL expected result by executing the reference through the
  production ``SandboxRunner``;
* writes Vietnamese drafts to a separate pending manifest and never imports
  them (there is no human-review flag for translations);
* removes a question it created if validation fails, so the clone stays clean.

Usage (from the backend directory):
    DATABASE_URL=postgresql://.../dbcas_clone \
        .venv/Scripts/python.exe ../_content/expansion-20261024/build.py \
        --spec ../_content/expansion-20261024/specs/pilot.py
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

from sqlalchemy import select

from app.benchmark import ROOT_DIR
from app.config import get_settings
from app.db import get_session_factory
from app.models import Account, Role
from app.repositories import CurriculumRepository, QuestionRepository
from app.schemas import QuestionUpsertRequest
from app.services import question_service as questions
from app.services.bank_validation import sql_fixture_problems
from app.services.rubric_validation import rubric_problems
from app.services.sandbox_runner import SandboxRunner


def _mask_url(url: str) -> str:
    parts = urlsplit(url)
    host = parts.hostname or "?"
    return f"{parts.scheme}://{parts.username or '?'}:***@{host}:{parts.port or 0}{parts.path}"


def _require_clone(settings) -> None:
    parts = urlsplit(settings.database_url)
    database = (parts.path or "").lstrip("/")
    if database != "dbcas_clone":
        raise SystemExit(
            f"Refusing to stage into database '{database or '?'}'. "
            "This builder only writes to the restored clone 'dbcas_clone'."
        )


def _load_spec(path: Path) -> list[dict]:
    spec_dir = str(path.parent.resolve())
    if spec_dir not in sys.path:
        sys.path.insert(0, spec_dir)
    module_spec = importlib.util.spec_from_file_location(
        f"expansion_spec_{path.stem}", path
    )
    if module_spec is None or module_spec.loader is None:
        raise SystemExit(f"Cannot load spec {path}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    items = getattr(module, "QUESTIONS", None)
    if not isinstance(items, list) or not items:
        raise SystemExit(f"Spec {path} must define a non-empty QUESTIONS list")
    return items


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _jsonable_expected(value, kind: str):
    if value is None:
        return None
    if kind == "number":
        number = Decimal(str(value))
        return int(number) if number == number.to_integral_value() else float(number)
    if kind == "boolean":
        return bool(value)
    return str(value)


def _compute_expected(runner: SandboxRunner, dataset: dict, reference: str,
                      ordered: bool, check_columns: bool) -> dict:
    schema = runner.provision_dataset(dataset["setup_sql"])
    try:
        result = runner.execute(reference, schema=schema)
    finally:
        runner.drop_dataset(schema)
    if not result.success:
        raise SystemExit(
            f"Reference failed on dataset '{dataset['dataset_name']}': "
            f"{result.error_type}: {result.error_message}"
        )
    rows = [
        [_jsonable_expected(value, kind) for value, kind in zip(row, result.column_types)]
        for row in result.rows
    ]
    return {
        "columns": list(result.columns),
        "rows": rows,
        "ordered": ordered,
        "check_columns": check_columns,
    }


def _preflight(item: dict, concept_ids: dict[str, int]) -> list[str]:
    problems: list[str] = []
    key = item.get("key")
    if not key:
        problems.append("missing key")
    if item.get("question_type") not in {"mcq", "sql", "essay"}:
        problems.append("invalid question_type")
    if not str(item.get("prompt", "")).strip():
        problems.append("empty prompt")
    if not str(item.get("explanation") or "").strip():
        problems.append("missing explanation")
    if not 1 <= int(item.get("difficulty_level", 0)) <= 5:
        problems.append("difficulty_level must be 1-5")
    try:
        if Decimal(str(item.get("points"))) <= 0:
            problems.append("points must be positive")
    except Exception:
        problems.append("invalid points")
    if not item.get("tags"):
        problems.append("missing tags")
    refs = item.get("source_refs") or []
    if not refs or any(not str(ref.get("url", "")).strip() for ref in refs):
        problems.append("missing source reference URL")
    for code in item.get("concept_codes", []):
        if code not in concept_ids:
            problems.append(f"unknown concept code {code}")
    if item.get("question_type") == "mcq":
        options = item.get("options") or []
        if len(options) < 2:
            problems.append("mcq needs at least 2 options")
        labels = [o.get("option_label", "").strip() for o in options]
        if len(labels) != len(set(labels)) or any(not label for label in labels):
            problems.append("mcq option labels must be unique and nonempty")
        texts = [o.get("option_text", "").strip() for o in options]
        if len(texts) != len(set(texts)) or any(not text for text in texts):
            problems.append("mcq option texts must be distinct and nonempty")
        if sum(1 for o in options if o.get("is_correct")) != 1:
            problems.append("mcq needs exactly one correct option")
    if item.get("question_type") == "sql":
        datasets = item.get("datasets") or []
        if len(datasets) < 2:
            problems.append("sql needs at least two datasets")
        if not any(d.get("is_edge_case") for d in datasets):
            problems.append("sql needs an edge-case dataset")
        names = [d.get("dataset_name") for d in datasets]
        if len(names) != len(set(names)):
            problems.append("sql dataset names must be unique")
        if not str(item.get("reference_answer") or "").strip():
            problems.append("sql needs a reference answer")
    if item.get("question_type") == "essay":
        rubrics = item.get("rubrics") or []
        problems.extend(rubric_problems(rubrics, item.get("points")))
    return problems


def _build_payload(item: dict, concept_ids: dict[str, int], datasets: list[dict]) -> QuestionUpsertRequest:
    payload = {
        "question_type": item["question_type"],
        "original_locale": item.get("original_locale", "en"),
        "prompt": item["prompt"],
        "reference_answer": item.get("reference_answer"),
        "explanation": item.get("explanation"),
        "tags": list(item.get("tags", [])),
        "source_refs": list(item.get("source_refs", [])),
        "difficulty_level": item["difficulty_level"],
        "points": item["points"],
        "concept_ids": [concept_ids[code] for code in item.get("concept_codes", [])],
        "required_concept_ids": [
            concept_ids[code] for code in item.get("required_concept_codes", [])
        ],
        "options": item.get("options", []),
        "datasets": datasets,
        "rubrics": item.get("rubrics", []),
        "translations": [],
    }
    return QuestionUpsertRequest(**payload)


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="Python spec defining QUESTIONS")
    parser.add_argument(
        "--report",
        default=str(ROOT_DIR / "_content/expansion-20261024/generated/staging_report.json"),
    )
    parser.add_argument(
        "--manifest",
        default=str(ROOT_DIR / "_content/expansion-20261024/generated/staging_manifest.json"),
    )
    parser.add_argument(
        "--translations-out",
        default=str(ROOT_DIR / "_content/expansion-20261024/generated/translations_vi_pending.json"),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    settings = get_settings()
    _require_clone(settings)
    print(f"Target: {_mask_url(settings.database_url)}")
    print(f"Sandbox: {_mask_url(settings.sandbox_url)}")

    spec_path = Path(args.spec).resolve()
    report_path = Path(args.report)
    manifest_path = Path(args.manifest)
    translations_path = Path(args.translations_out)
    items = _load_spec(spec_path)
    spec_dir = str(spec_path.parent.resolve())
    if spec_dir not in sys.path:
        sys.path.insert(0, spec_dir)
    from lib import normalize_items

    items = normalize_items(items)
    if args.limit:
        items = items[: args.limit]
    keys = [item.get("key") for item in items]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise SystemExit(f"Duplicate spec keys: {duplicates}")

    manifest = {"spec": str(spec_path), "questions": {}}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.setdefault("questions", {})
    pending_translations = {
        "version": "2026-10-24-expansion-pending",
        "locale": "vi",
        "review_status": "pending_human_review",
        "imported": False,
        "note": (
            "Machine-assisted drafts only. No human reviewer has approved "
            "these translations, so they are deliberately not imported."
        ),
        "questions": {},
    }
    if translations_path.exists():
        existing = json.loads(translations_path.read_text(encoding="utf-8"))
        pending_translations["questions"] = existing.get("questions", {})

    runner = SandboxRunner(settings)
    session_factory = get_session_factory()
    db = session_factory()
    report = {
        "spec": str(spec_path),
        "target": _mask_url(settings.database_url),
        "sandbox": _mask_url(settings.sandbox_url),
        "dry_run": args.dry_run,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "questions": [],
    }
    try:
        admin = db.scalar(
            select(Account)
            .join(Account.roles)
            .where(Role.role_name == "Administrator")
            .order_by(Account.account_id)
            .limit(1)
        )
        if admin is None:
            raise SystemExit("No Administrator account exists in the clone")
        concepts = {
            concept.concept_code: concept
            for concept in CurriculumRepository(db).list_concepts()
        }
        concept_ids = {
            code: concept.concept_id for code, concept in concepts.items()
        }
        qrepo = QuestionRepository(db)

        for item in items:
            key = item["key"]
            entry = {
                "key": key,
                "question_type": item.get("question_type"),
                "difficulty_level": item.get("difficulty_level"),
                "concept_codes": item.get("concept_codes", []),
                "status": "pending",
            }
            problems = _preflight(item, concept_ids)
            if problems:
                entry.update(status="rejected", problems=problems)
                report["questions"].append(entry)
                continue

            datasets: list[dict] = []
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
                required_features = [
                    concepts[code].sql_feature
                    for code in item.get("required_concept_codes", [])
                ]
                fixture_problems = sql_fixture_problems(
                    [
                        SimpleNamespace(
                            dataset_name=d["dataset_name"],
                            setup_sql=d["setup_sql"],
                            expected_result=d["expected_result"],
                            is_edge_case=d["is_edge_case"],
                        )
                        for d in datasets
                    ],
                    item["reference_answer"],
                    required_features,
                )
                if fixture_problems:
                    entry.update(status="rejected", problems=list(fixture_problems))
                    report["questions"].append(entry)
                    continue

            payload = _build_payload(item, concept_ids, datasets)

            existing = [
                q
                for q in qrepo.search(question_type=item["question_type"])
                if q.prompt == item["prompt"]
            ]
            if existing:
                entry.update(
                    status="skipped_existing_prompt",
                    existing_question_ids=[q.question_id for q in existing],
                )
                report["questions"].append(entry)
                continue

            if args.dry_run:
                entry.update(
                    status="dry_run_ok",
                    datasets=[
                        {"dataset_name": d["dataset_name"], "rows": len(d["expected_result"]["rows"])}
                        for d in datasets
                    ],
                )
                report["questions"].append(entry)
                continue

            detail = questions.create_question(db, payload, admin)
            entry["question_id"] = detail.question_id
            try:
                validated = questions.set_question_status(
                    db, detail.question_id, "validated", runner
                )
                entry.update(status="validated", question_status=validated.status)
            except Exception as exc:  # noqa: BLE001 - report then clean up the clone
                entry.update(
                    status="validation_failed",
                    problems=[str(getattr(exc, "message", exc))],
                )
                try:
                    questions.delete_question(db, detail.question_id)
                    entry["cleanup"] = "deleted"
                except Exception as cleanup_error:  # noqa: BLE001
                    entry["cleanup"] = f"failed: {cleanup_error}"
                report["questions"].append(entry)
                continue

            manifest["questions"][key] = {
                "question_id": detail.question_id,
                "prompt_sha256": _prompt_hash(item["prompt"]),
                "question_type": item["question_type"],
                "staged_at": datetime.now(timezone.utc).isoformat(),
            }
            _write_json(manifest_path, manifest)

            draft = item.get("vi_draft")
            if draft:
                pending_translations["questions"][key] = {
                    "question_id": detail.question_id,
                    "source_sha256": _prompt_hash(item["prompt"]),
                    "review_status": "pending_human_review",
                    **draft,
                }
                _write_json(translations_path, pending_translations)
                entry["vi_translation"] = "draft_pending_human_review_not_imported"
            report["questions"].append(entry)
            print(f"[{entry['status']}] {key} -> question {detail.question_id}")
    finally:
        db.close()

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["summary"] = {
        status: sum(1 for q in report["questions"] if q["status"] == status)
        for status in sorted({q["status"] for q in report["questions"]})
    }
    _write_json(report_path, report)
    print(json.dumps(report["summary"], indent=2))
    return 0 if not any(
        q["status"] in {"rejected", "validation_failed"} for q in report["questions"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
