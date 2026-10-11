"""Import the reviewed academic curriculum pack without learner data or resets."""
import argparse
import json

from .config import ROOT_DIR, get_settings
from .db import get_session_factory
from .errors import AppError
from .repositories import AccountRepository, CurriculumRepository, QuestionRepository, AssessmentRepository
from .schemas import ConceptUpsertRequest, CloUpsertRequest, QuestionUpsertRequest, AssessmentUpsertRequest
from .services import curriculum_service as curriculum, concept_graph_service as graph
from .services import question_service as questions, assessment_service as assessments
from .services.sandbox_runner import SandboxRunner


def import_pack(db, admin, runner, pack=None):
    if not any(role.role_name == "Administrator" for role in admin.roles):
        raise AppError(403, "admin_required", "The pack requires an existing administrator")
    pack = pack or json.loads((ROOT_DIR / "db/benchmark_pack.json").read_text(encoding="utf-8"))
    crepo, qrepo, arepo = CurriculumRepository(db), QuestionRepository(db), AssessmentRepository(db)
    ids = {}
    for item in pack["concepts"]:
        existing = crepo.find_concept_by_code(item["concept_code"])
        if existing:
            if existing.sql_feature != item.get("sql_feature"):
                raise AppError(409, "benchmark_concept_conflict", f"Review SQL metadata for {item['concept_code']} before importing")
            ids[item["concept_code"]] = existing.concept_id
        else:
            result = curriculum.create_concept(db, ConceptUpsertRequest(**item))
            ids[item["concept_code"]] = result.concept_id
    for item in pack["clos"]:
        existing = crepo.find_clo_by_code(item["clo_code"])
        clo = existing or curriculum.create_clo(db, CloUpsertRequest(**item), admin)
        curriculum.set_clo_concepts(db, clo.clo_id, [ids[code] for code in item["concept_codes"]])
    for code, prerequisites in pack["dependencies"].items():
        graph.set_concept_prerequisites(db, ids[code], [ids[c] for c in prerequisites])
    question_ids = []
    for item in pack["questions"]:
        matches = [q for q in qrepo.search(q=item["prompt"], question_type=item["question_type"])
                   if q.prompt == item["prompt"] and q.status == "validated"]
        if matches:
            question_ids.append(matches[-1].question_id)
            continue
        payload = QuestionUpsertRequest(**{**item,
            "concept_ids": [ids[code] for code in item["concept_codes"]],
            "required_concept_ids": [ids[code] for code in item.get("required_concept_codes", [])]})
        question = questions.create_question(db, payload, admin)
        questions.set_question_status(db, question.question_id, "validated", runner)
        question_ids.append(question.question_id)
    assessment_ids = []
    for item in pack["assessments"]:
        existing = next((a for a in arepo.list_assessments() if a.title == item["title"] and a.status == "published"), None)
        if existing:
            from .services.assessment_validation import validate_assessment_bank
            validate_assessment_bank(db, existing, runner)
            assessment_ids.append(existing.assessment_id)
            continue
        payload = AssessmentUpsertRequest(**{**item, "concepts": [
            {"concept_id": ids[code], "target_pct": item["target_pct"], "min_difficulty": 1, "max_difficulty": 5}
            for code in item["concept_codes"]]})
        assessment = assessments.create_assessment(db, payload, admin)
        assessments.set_assessment_status(db, assessment.assessment_id, "published", runner)
        assessment_ids.append(assessment.assessment_id)
    return {"concept_ids": ids, "question_ids": question_ids, "assessment_ids": assessment_ids}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admin-email", required=True, help="Existing administrator; no account is provisioned")
    args = parser.parse_args()
    with get_session_factory()() as db:
        admin = AccountRepository(db).find_by_email(args.admin_email.strip().lower())
        if admin is None:
            raise SystemExit("Administrator account not found")
        result = import_pack(db, admin, SandboxRunner(get_settings()))
        print(f"Benchmark ready: {len(result['concept_ids'])} concepts, {len(result['question_ids'])} questions; assessment IDs {result['assessment_ids']}")


if __name__ == "__main__":
    main()
