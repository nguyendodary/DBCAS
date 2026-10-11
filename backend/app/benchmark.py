"""Import the reviewed academic curriculum pack without learner data or resets."""
import argparse
import json

from .config import ROOT_DIR, get_settings
from .db import get_session_factory
from .errors import AppError
from .repositories import AccountRepository, CurriculumRepository, QuestionRepository, AssessmentRepository, ConceptGraphRepository
from .schemas import ConceptUpsertRequest, CloUpsertRequest, QuestionUpsertRequest, AssessmentUpsertRequest
from .services import curriculum_service as curriculum, concept_graph_service as graph
from .services import question_service as questions, assessment_service as assessments
from .services.sandbox_runner import SandboxRunner


def import_pack(db, admin, runner, pack=None, *, fill_missing_techniques=False):
    if not any(role.role_name == "Administrator" for role in admin.roles):
        raise AppError(403, "admin_required", "The pack requires an existing administrator")
    pack = pack or json.loads((ROOT_DIR / "db/benchmark_pack.json").read_text(encoding="utf-8"))
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
    for item in pack["questions"]:
        payload = QuestionUpsertRequest(**{**item,
            "concept_ids": [ids[code] for code in item["concept_codes"]],
            "required_concept_ids": [ids[code] for code in item.get("required_concept_codes", [])]})
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
                return value
            if normalized(actual.model_dump()) != normalized(payload.model_dump()):
                raise AppError(409, "benchmark_question_conflict", "An existing benchmark prompt has different content; review it before importing")
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
    return {"concept_ids": ids, "question_ids": question_ids, "assessment_ids": assessment_ids}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admin-email", required=True, help="Existing administrator; no account is provisioned")
    parser.add_argument("--fill-missing-techniques", action="store_true", help="Add reviewed SQL technique metadata only where an existing matching concept has none")
    args = parser.parse_args()
    with get_session_factory()() as db:
        admin = AccountRepository(db).find_by_email(args.admin_email.strip().lower())
        if admin is None:
            raise SystemExit("Administrator account not found")
        result = import_pack(db, admin, SandboxRunner(get_settings()), fill_missing_techniques=args.fill_missing_techniques)
        print(f"Benchmark ready: {len(result['concept_ids'])} concepts, {len(result['question_ids'])} questions; assessment IDs {result['assessment_ids']}")


if __name__ == "__main__":
    main()
