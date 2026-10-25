"""Authorized activation importer for the 271 staged questions.

This is the persistent-database importer anticipated by the readiness report.
It deliberately does not reuse ``build.py``'s clone guard; instead it requires
an explicit confirmation, a verified pre-activation backup and a database name
of ``dbcas`` (or an explicitly rehearsed ``dbcas_rehearsal*`` database).

It imports questions through the production service, validates each through
``set_question_status`` (including sandbox SQL verification), imports the
machine-verified Vietnamese drafts through ``upsert_question_translations`` so
the source fingerprint is recomputed, and seeds the 49 technical blueprints
with ``approved_by = NULL``.

Legacy repairs are not applied. Q5 is retired historical content and is never
written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import select, text

ROOT = Path(__file__).resolve().parents[2]
EXPANSION = ROOT / "_content/expansion-20261024"
SPECS = EXPANSION / "specs"
GENERATED = EXPANSION / "generated"
EVIDENCE = EXPANSION / "evidence"
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(EXPANSION))
sys.path.insert(0, str(SPECS))

import build  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import get_session_factory  # noqa: E402
from app.models import Account, Role  # noqa: E402
from app.repositories import CurriculumRepository, QuestionRepository  # noqa: E402
from app.services import question_service as questions  # noqa: E402
from app.services.bank_validation import sql_fixture_problems  # noqa: E402
from app.services.blueprints import ensure_all_blueprints  # noqa: E402
from app.services.question_localization import (  # noqa: E402
    source_fingerprint,
    translation_is_current,
)
from app.services.sandbox_runner import SandboxRunner  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _target_database(settings) -> str:
    return (urlsplit(settings.database_url).path or "").lstrip("/")


def _require_authorized_target(settings, args) -> None:
    database = _target_database(settings)
    if database == "dbcas":
        if not args.confirm:
            raise SystemExit("Refusing persistent activation without --confirm")
        if not args.backup or not args.backup_sha256:
            raise SystemExit("Persistent activation requires --backup and --backup-sha256")
        backup = Path(args.backup)
        if not backup.exists():
            raise SystemExit(f"Backup not found: {backup}")
        actual = _sha256(backup)
        if actual != args.backup_sha256:
            raise SystemExit(
                f"Backup checksum mismatch: expected {args.backup_sha256}, got {actual}"
            )
        if backup.stat().st_mtime > args.started.timestamp():
            raise SystemExit("Backup must have been created before this activation run")
        return
    if database.startswith("dbcas_rehearsal"):
        if not args.rehearsal or not args.confirm:
            raise SystemExit("Rehearsal requires --rehearsal and --confirm")
        return
    raise SystemExit(
        f"Refusing to import into '{database or '?'}'. Allowed: dcas or a "
        "dbcas_rehearsal* database with --rehearsal."
    )


def _load_specs() -> tuple[list[dict], dict[int, dict]]:
    evidence = json.loads((EVIDENCE / "review_repairs.json").read_text(encoding="utf-8"))
    spec_files = evidence["spec_files"]
    items: list[dict] = []
    for name in spec_files:
        path = SPECS / name
        loaded = build._load_spec(path)
        from lib import normalize_items

        items.extend(normalize_items(loaded))
    keys = [item.get("key") for item in items]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise SystemExit(f"Duplicate spec keys: {duplicates}")
    manifest = json.loads((GENERATED / "staging_manifest.json").read_text(encoding="utf-8"))
    pending = json.loads(
        (GENERATED / "translations_vi_pending.json").read_text(encoding="utf-8")
    )
    expected = set(manifest["questions"]) | set(pending["questions"])
    if set(keys) != set(manifest["questions"]) or set(keys) != set(pending["questions"]):
        raise SystemExit(
            "Specs, staging manifest and pending translations do not cover the same keys"
        )
    if len(expected) != 271 or len(items) != 271:
        raise SystemExit(f"Expected 271 staged items, found {len(items)}")
    return items, pending["questions"]


def _historical_digest(db, sql: str) -> str:
    return db.execute(text(sql)).scalar() or ""


def _snapshot_history(db) -> dict:
    return {
        "questions_le_450": _historical_digest(
            db,
            "select md5(coalesce(string_agg(md5(to_jsonb(t)::text), '' "
            "order by md5(to_jsonb(t)::text)), '')) from question t "
            "where question_id <= 450",
        ),
        "q5": _historical_digest(
            db,
            "select md5(to_jsonb(t)::text) from question t where question_id = 5",
        ),
        "sessions": _historical_digest(
            db,
            "select md5(coalesce(string_agg(md5(to_jsonb(t)::text), '' "
            "order by md5(to_jsonb(t)::text)), '')) from assessment_session t",
        ),
        "attempts": _historical_digest(
            db,
            "select md5(coalesce(string_agg(md5(to_jsonb(t)::text), '' "
            "order by md5(to_jsonb(t)::text)), '')) from attempt t",
        ),
        "selection_log": _historical_digest(
            db,
            "select md5(coalesce(string_agg(md5(to_jsonb(t)::text), '' "
            "order by md5(to_jsonb(t)::text)), '')) from selection_log t",
        ),
        "translations_le_450": _historical_digest(
            db,
            "select md5(coalesce(string_agg(md5(to_jsonb(t)::text), '' "
            "order by md5(to_jsonb(t)::text)), '')) from question_translation t "
            "where question_id <= 450",
        ),
    }


def _preflight_translation(entry: dict) -> list[str]:
    problems = []
    if entry.get("review_status") != "pending_human_review":
        problems.append("unexpected_review_status")
    if not str(entry.get("prompt") or "").strip():
        problems.append("missing_prompt")
    if not str(entry.get("explanation") or "").strip():
        problems.append("missing_explanation")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--rehearsal", action="store_true")
    parser.add_argument("--backup")
    parser.add_argument("--backup-sha256")
    parser.add_argument(
        "--report",
        default=str(EVIDENCE / "activation_import_report.json"),
    )
    parser.add_argument(
        "--manifest",
        default=str(GENERATED / "activation_manifest.json"),
    )
    parser.add_argument(
        "--translations-out",
        default=str(GENERATED / "translations_vi_activated.json"),
    )
    args = parser.parse_args()
    args.started = datetime.now(timezone.utc)

    settings = get_settings()
    _require_authorized_target(settings, args)
    database = _target_database(settings)
    print(f"Target: {database}")

    items, pending = _load_specs()
    for key, entry in pending.items():
        problems = _preflight_translation(entry)
        if problems:
            raise SystemExit(f"Pending translation {key} is incomplete: {problems}")

    runner = SandboxRunner(settings)
    db = get_session_factory()()
    report = {
        "started_at": args.started.isoformat(),
        "target": database,
        "backup_sha256": args.backup_sha256,
        "rehearsal": args.rehearsal,
        "questions": [],
        "translations": [],
        "blueprints": None,
        "history": {"before": None, "after": None, "unchanged": None},
    }
    try:
        migration = db.execute(
            text("select version from schema_migration order by version desc limit 1")
        ).scalar()
        if migration != "013_assessment_blueprints.sql":
            raise SystemExit(
                f"Migration 013 must be applied first; current latest is {migration!r}"
            )
        if not db.scalar(text("select to_regclass('public.assessment_blueprint')")):
            raise SystemExit("assessment_blueprint table is missing")

        report["history"]["before"] = _snapshot_history(db)
        admin = db.scalar(
            select(Account)
            .join(Account.roles)
            .where(Role.role_name == "Administrator")
            .order_by(Account.account_id)
            .limit(1)
        )
        if admin is None:
            raise SystemExit("No Administrator account exists")
        concepts = {
            concept.concept_code: concept
            for concept in CurriculumRepository(db).list_concepts()
        }
        concept_ids = {code: concept.concept_id for code, concept in concepts.items()}
        qrepo = QuestionRepository(db)
        activation_manifest = {
            "version": "2026-10-25-activation",
            "target": database,
            "created_at": args.started.isoformat(),
            "questions": {},
        }
        if Path(args.manifest).exists():
            loaded = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
            if loaded.get("target") == database:
                activation_manifest = loaded
            else:
                # A manifest from another database (for example a prior
                # rehearsal) must not pin question IDs in this target.
                activation_manifest["questions"] = {}
            activation_manifest["target"] = database

        created = skipped = translated = 0
        failures = []
        for item in items:
            key = item["key"]
            entry = {
                "key": key,
                "question_type": item.get("question_type"),
                "difficulty_level": item.get("difficulty_level"),
            }
            problems = build._preflight(item, concept_ids)
            if problems:
                failures.append({"key": key, "stage": "preflight", "problems": problems})
                entry.update(status="rejected", problems=problems)
                report["questions"].append(entry)
                continue

            prompt_hash = build._prompt_hash(item["prompt"])
            if prompt_hash != pending[key]["source_sha256"]:
                failures.append(
                    {"key": key, "stage": "prompt_hash", "problems": ["spec_manifest_drift"]}
                )
                entry.update(status="rejected", problems=["spec_manifest_drift"])
                report["questions"].append(entry)
                continue

            existing_id = None
            question = None
            mapped = activation_manifest["questions"].get(key)
            if mapped:
                existing_id = mapped.get("question_id")
            if existing_id is not None:
                question = qrepo.get_detail(existing_id)
                if question is None or question.prompt != item["prompt"]:
                    # A stale mapping must never pin this import: drop it and
                    # fall back to prompt lookup (or creation) in this target.
                    activation_manifest["questions"].pop(key, None)
                    existing_id = None
                    question = None
            if existing_id is None:
                matches = [
                    q
                    for q in qrepo.search(question_type=item["question_type"])
                    if q.prompt == item["prompt"]
                ]
                if matches:
                    existing_id = matches[0].question_id
                    question = qrepo.get_detail(existing_id)

            if existing_id is not None:
                if question.status != "validated":
                    try:
                        questions.set_question_status(
                            db, question.question_id, "validated", runner
                        )
                        question = qrepo.get_detail(existing_id)
                    except Exception as exc:  # noqa: BLE001
                        failures.append(
                            {
                                "key": key,
                                "stage": "revalidate",
                                "problems": [str(getattr(exc, "message", exc))],
                            }
                        )
                        entry.update(status="revalidation_failed")
                        report["questions"].append(entry)
                        continue
                skipped += 1
                entry.update(status="skipped_existing_prompt", question_id=existing_id)
            else:
                datasets = []
                if item["question_type"] == "sql":
                    ordered = bool(item.get("ordered", True))
                    check_columns = bool(item.get("check_columns", True))
                    for dataset in item["datasets"]:
                        expected = build._compute_expected(
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
                            build.SimpleNamespace(
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
                        failures.append(
                            {"key": key, "stage": "fixtures", "problems": list(fixture_problems)}
                        )
                        entry.update(status="rejected", problems=list(fixture_problems))
                        report["questions"].append(entry)
                        continue
                payload = build._build_payload(item, concept_ids, datasets)
                detail = questions.create_question(db, payload, admin)
                try:
                    questions.set_question_status(
                        db, detail.question_id, "validated", runner
                    )
                except Exception as exc:  # noqa: BLE001
                    failures.append(
                        {
                            "key": key,
                            "stage": "validation",
                            "problems": [str(getattr(exc, "message", exc))],
                        }
                    )
                    try:
                        questions.delete_question(db, detail.question_id)
                        entry["cleanup"] = "deleted"
                    except Exception as cleanup_error:  # noqa: BLE001
                        entry["cleanup"] = f"failed: {cleanup_error}"
                    entry.update(status="validation_failed")
                    report["questions"].append(entry)
                    continue
                existing_id = detail.question_id
                created += 1
                entry.update(status="validated", question_id=existing_id)

            question = qrepo.get_detail(existing_id)
            draft = pending[key]
            translation = {
                "locale": "vi",
                "prompt": draft["prompt"],
                "explanation": draft["explanation"],
                "option_texts": draft.get("option_texts") or {},
                "rubrics": draft.get("rubrics") or {},
            }
            try:
                questions.upsert_question_translations(db, question, [translation])
                db.commit()
                question = qrepo.get_detail(existing_id)
                row = next(
                    (t for t in question.translations if t.locale == "vi"), None
                )
                if row is None or not translation_is_current(question, row):
                    raise RuntimeError("translation is not current after upsert")
                translated += 1
                entry["translation"] = "current"
                entry["source_fingerprint"] = source_fingerprint(question)
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                failures.append(
                    {
                        "key": key,
                        "stage": "translation",
                        "problems": [str(getattr(exc, "message", exc))],
                    }
                )
                entry["translation"] = "failed"
                entry["translation_error"] = str(getattr(exc, "message", exc))

            activation_manifest["questions"][key] = {
                "question_id": existing_id,
                "prompt_sha256": prompt_hash,
                "question_type": item["question_type"],
                "translation": entry.get("translation"),
            }
            build._write_json(Path(args.manifest), activation_manifest)
            report["questions"].append(entry)
            print(f"[{entry['status']}] {key} -> {existing_id} ({entry.get('translation')})")

        report["translations"] = [
            {
                "key": key,
                "question_id": mapping["question_id"],
                "review_status": "machine_verified_not_human_reviewed",
                "imported": mapping.get("translation") == "current",
            }
            for key, mapping in activation_manifest["questions"].items()
        ]
        build._write_json(
            Path(args.translations_out),
            {
                "version": "2026-10-25-activation",
                "locale": "vi",
                "review_status": "machine_verified_not_human_reviewed",
                "human_reviewed": False,
                "imported": True,
                "note": (
                    "Machine-verified translations imported through the production "
                    "fingerprint check. They are not human-reviewed."
                ),
                "questions": {
                    key: {
                        "question_id": mapping["question_id"],
                        "review_status": "machine_verified_not_human_reviewed",
                        "imported": mapping.get("translation") == "current",
                    }
                    for key, mapping in activation_manifest["questions"].items()
                },
            },
        )

        if failures:
            report["blueprints"] = {"status": "skipped_due_to_failures"}
        else:
            created_blueprints = ensure_all_blueprints(db, approved_by=None)
            db.commit()
            total_blueprints = db.execute(
                text("select count(*) from assessment_blueprint")
            ).scalar()
            report["blueprints"] = {
                "created_this_run": len(created_blueprints),
                "total": total_blueprints,
                "approved_by_null": db.execute(
                    text("select count(*) from assessment_blueprint where approved_by is not null")
                ).scalar()
                == 0,
            }

        report["history"]["after"] = _snapshot_history(db)
        report["history"]["unchanged"] = (
            report["history"]["before"] == report["history"]["after"]
        )
        report["summary"] = {
            "created": created,
            "skipped": skipped,
            "translated": translated,
            "failures": len(failures),
        }
        report["failures"] = failures
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        report["verdict"] = (
            "pass"
            if not failures
            and report["history"]["unchanged"]
            and report["blueprints"]
            and report["blueprints"].get("total") == 49
            and report["blueprints"].get("approved_by_null")
            else "fail"
        )
        build._write_json(Path(args.report), report)
        print(json.dumps(report["summary"], indent=2))
        print(f"Blueprints: {report['blueprints']}")
        print(f"Historical rows unchanged: {report['history']['unchanged']}")
        print(f"Verdict: {report['verdict']}")
        return 0 if report["verdict"] == "pass" else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
