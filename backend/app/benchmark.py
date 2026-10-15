"""Import the reviewed academic curriculum pack without learner data or resets."""
import argparse
import json
from types import SimpleNamespace

from .config import ROOT_DIR, get_settings
from .db import get_session_factory
from .errors import AppError
from .repositories import AccountRepository, CurriculumRepository, QuestionRepository, AssessmentRepository, ConceptGraphRepository
from .schemas import ConceptUpsertRequest, CloUpsertRequest, QuestionUpsertRequest, AssessmentUpsertRequest
from .services import curriculum_service as curriculum, concept_graph_service as graph
from .services import question_service as questions, assessment_service as assessments
from .services.question_localization import translation_problems
from .services.sandbox_runner import SandboxRunner


def _translation_manifest(pack):
    manifest_name = pack.get("translations_manifest")
    if not manifest_name:
        raise AppError(422, "invalid_translation_manifest", "The question pack must reference its versioned Vietnamese translation manifest")
    manifest_path = (ROOT_DIR / manifest_name).resolve()
    if ROOT_DIR.resolve() not in manifest_path.parents:
        raise AppError(422, "invalid_translation_manifest", "The translation manifest must be inside the repository")
    try:
        translations = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AppError(422, "invalid_translation_manifest", "The question translation manifest could not be read") from exc
    if translations.get("locale") != "vi" or not isinstance(translations.get("questions"), dict):
        raise AppError(422, "invalid_translation_manifest", "The question translation manifest must contain a Vietnamese question map")
    return translations


def _validate_pack_translations(pack, translations):
    """Reject incomplete/unsafe packs before any curriculum rows are written."""
    questions_in_pack = pack.get("questions", [])
    keys = [item.get("key") for item in questions_in_pack]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    missing = sorted(key or "<missing-key>" for key in keys if not key or key not in translations["questions"])
    errors = []
    for item in questions_in_pack:
        key = item.get("key")
        translated = translations["questions"].get(key)
        if not translated:
            continue
        question = SimpleNamespace(
            question_type=item["question_type"],
            prompt=item["prompt"],
            explanation=item.get("explanation"),
            options=[SimpleNamespace(option_label=row["option_label"], option_text=row["option_text"])
                     for row in item.get("options", [])],
            rubrics=[SimpleNamespace(level_name=row["level_name"], criteria=row["criteria"])
                     for row in item.get("rubrics", [])],
        )
        errors.extend(f"{key}: {problem}" for problem in translation_problems(question, translated))
    if duplicates or missing or errors:
        details = ([{"duplicate_key": key} for key in duplicates]
                   + [{"missing_translation": key} for key in missing]
                   + [{"invalid_translation": problem} for problem in errors])
        raise AppError(
            422,
            "question_translation_incomplete",
            "The question pack must have one valid Vietnamese translation per question before import",
            details=details,
        )


def import_pack(db, admin, runner, pack=None, *, fill_missing_techniques=False, translation_data=None,
                repair_legacy_index_rubric=False):
    if not any(role.role_name == "Administrator" for role in admin.roles):
        raise AppError(403, "admin_required", "The pack requires an existing administrator")
    pack = pack or json.loads((ROOT_DIR / "db/benchmark_pack.json").read_text(encoding="utf-8"))
    translations = translation_data if translation_data is not None else _translation_manifest(pack)
    _validate_pack_translations(pack, translations)
    crepo, qrepo, arepo = CurriculumRepository(db), QuestionRepository(db), AssessmentRepository(db)
    ids = {}
    for item in pack["concepts"]:
        existing = crepo.find_concept_by_code(item["concept_code"])
        if existing:
            if fill_missing_techniques and existing.sql_feature is None and item.get("sql_feature"):
                existing.sql_feature = item["sql_feature"]
                db.commit()
            if existing.sql_feature != item.get("sql_feature"):
                raise AppError(409, "benchmark_concept_conflict", f"Review SQL metadata for {item['concept_code']} before importing")
            ids[item["concept_code"]] = existing.concept_id
        else:
            result = curriculum.create_concept(db, ConceptUpsertRequest(**item))
            ids[item["concept_code"]] = result.concept_id
    for item in pack["clos"]:
        existing = crepo.find_clo_by_code(item["clo_code"])
        clo = existing or curriculum.create_clo(db, CloUpsertRequest(**item), admin)
        # Import is additive: existing mappings and AI review decisions survive.
        linked = {link.concept_id for link in crepo.links_for_clo(clo.clo_id)}
        curriculum.set_clo_concepts(db, clo.clo_id, sorted(linked | {ids[code] for code in item["concept_codes"]}))
    for code, prerequisites in pack["dependencies"].items():
        existing = {edge.prerequisite_concept_id for edge in ConceptGraphRepository(db).prerequisites_of(ids[code])}
        graph.set_concept_prerequisites(db, ids[code], sorted(existing | {ids[c] for c in prerequisites}))
    question_ids = []
    localized_count = 0
    missing_translation_keys = []
    for item in pack["questions"]:
        translated = translations["questions"].get(item.get("key"))
        translation_rows = [{"locale": "vi", **translated}] if translated else []
        payload = QuestionUpsertRequest(**{**item,
            "concept_ids": [ids[code] for code in item["concept_codes"]],
            "required_concept_ids": [ids[code] for code in item.get("required_concept_codes", [])],
            "translations": translation_rows})
        if translated:
            localized_count += 1
        else:
            missing_translation_keys.append(item.get("key", item["prompt"]))
        matches = [q for q in qrepo.search(q=item["prompt"], question_type=item["question_type"])
                   if q.prompt == item["prompt"] and q.status == "validated"]
        if matches:
            detail = questions.get_question(db, matches[-1].question_id)
            actual = QuestionUpsertRequest(**{**detail.model_dump(),
                "concept_ids": [tag.concept_id for tag in detail.concepts if tag.confirmed],
                "required_concept_ids": [tag.concept_id for tag in detail.concepts if tag.confirmed and tag.is_required]})
            def normalized(value):
                # Child collection order is incidental; expected-result row
                # order and all nested fixture content remain significant.
                for field in ("concept_ids", "required_concept_ids", "options", "datasets", "rubrics"):
                    value[field] = sorted(value[field], key=lambda v: json.dumps(v, sort_keys=True, default=str))
                value.pop("translations", None)
                return value
            if normalized(actual.model_dump()) != normalized(payload.model_dump()):
                from .services.legacy_rubric_repair import repair_index_rubric
                if not repair_legacy_index_rubric or not repair_index_rubric(
                        db, qrepo, matches[-1], item, actual, payload):
                    raise AppError(409, "benchmark_question_conflict", "An existing benchmark prompt has different content; review it before importing")
            questions.upsert_question_translations(db, matches[-1], payload.translations)
            db.commit()
            question_ids.append(matches[-1].question_id)
            continue
        question = questions.create_question(db, payload, admin)
        questions.set_question_status(db, question.question_id, "validated", runner)
        question_ids.append(question.question_id)
    assessment_ids = []
    for item in pack["assessments"]:
        payload = AssessmentUpsertRequest(**{**item, "concepts": [
            {"concept_id": ids[code], "target_pct": item["target_pct"], "min_difficulty": 1, "max_difficulty": 5}
            for code in item["concept_codes"]]})
        existing = next((a for a in arepo.list_assessments() if a.title == item["title"] and a.status == "published"), None)
        if existing:
            existing = arepo.get_assessment(existing.assessment_id)
            actual = AssessmentUpsertRequest(**{field: getattr(existing, field) for field in (
                "title", "description", "duration_min", "max_questions", "target_mcq", "target_sql", "target_essay")},
                concepts=[{"concept_id": target.concept_id, "target_pct": target.target_pct,
                    "min_difficulty": target.min_difficulty, "max_difficulty": target.max_difficulty} for target in existing.targets])
            expected, current = payload.model_dump(), actual.model_dump()
            for value in (expected, current):
                value["concepts"].sort(key=lambda target: target["concept_id"])
            if expected != current:
                raise AppError(409, "benchmark_assessment_conflict", "An existing benchmark assessment has different configuration; review it before importing")
            from .services.assessment_validation import validate_assessment_bank
            validate_assessment_bank(db, existing, runner)
            assessment_ids.append(existing.assessment_id)
            continue
        assessment = assessments.create_assessment(db, payload, admin)
        assessments.set_assessment_status(db, assessment.assessment_id, "published", runner)
        assessment_ids.append(assessment.assessment_id)
    return {"concept_ids": ids, "question_ids": question_ids, "assessment_ids": assessment_ids,
            "localized_count": localized_count, "missing_translation_keys": missing_translation_keys}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admin-email", required=True, help="Existing administrator; no account is provisioned")
    parser.add_argument("--fill-missing-techniques", action="store_true", help="Add reviewed SQL technique metadata only where an existing matching concept has none")
    parser.add_argument("--include-sql-knowledge", action="store_true", help="Add reviewed MCQ/essay DML and DDL knowledge; SQL execution stays read-only")
    parser.add_argument("--include-postgres-knowledge", action="store_true", help="Add the official PostgreSQL extended question pack (db/postgres_knowledge_pack.json)")
    parser.add_argument("--repair-legacy-index-rubric", action="store_true",
                        help="Explicitly apply the reviewed repair to the exact historical index essay; require existing attempt snapshots")
    args = parser.parse_args()
    selected_packs = [("db/benchmark_pack.json", json.loads((ROOT_DIR / "db/benchmark_pack.json").read_text(encoding="utf-8")))]
    if args.include_sql_knowledge:
        selected_packs.append(("db/sql_knowledge_pack.json", json.loads((ROOT_DIR / "db/sql_knowledge_pack.json").read_text(encoding="utf-8"))))
    if args.include_postgres_knowledge:
        selected_packs.append(("db/postgres_knowledge_pack.json", json.loads((ROOT_DIR / "db/postgres_knowledge_pack.json").read_text(encoding="utf-8"))))
    prepared = []
    for path, pack in selected_packs:
        translations = _translation_manifest(pack)
        _validate_pack_translations(pack, translations)
        prepared.append((path, pack, translations))
    with get_session_factory()() as db:
        admin = AccountRepository(db).find_by_email(args.admin_email.strip().lower())
        if admin is None:
            raise SystemExit("Administrator account not found")
        runner = SandboxRunner(get_settings())
        result = import_pack(db, admin, runner, prepared[0][1], translation_data=prepared[0][2], fill_missing_techniques=args.fill_missing_techniques,
                             repair_legacy_index_rubric=args.repair_legacy_index_rubric)
        for _, pack, translations in prepared[1:]:
            supplement = import_pack(db, admin, runner, pack, translation_data=translations, fill_missing_techniques=args.fill_missing_techniques)
            result["concept_ids"].update(supplement["concept_ids"])
            result["question_ids"].extend(supplement["question_ids"])
            result["assessment_ids"].extend(supplement["assessment_ids"])
            result["localized_count"] += supplement["localized_count"]
            result["missing_translation_keys"].extend(supplement["missing_translation_keys"])
        print(f"Benchmark ready: {len(result['concept_ids'])} concepts, {len(result['question_ids'])} questions; Vietnamese content {result['localized_count']}/{len(result['question_ids'])}; missing translations {len(result['missing_translation_keys'])}; assessment IDs {result['assessment_ids']}")


if __name__ == "__main__":
    main()
