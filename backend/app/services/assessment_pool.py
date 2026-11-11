"""Optional administrator-curated assessment pool, preserving adaptive selection."""
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from ..errors import AppError
from ..models import Assessment, AssessmentQuestion
from ..repositories import AssessmentRepository


def get_pool(db, assessment_id):
    if AssessmentRepository(db).get_assessment(assessment_id) is None:
        raise AppError(404, "assessment_not_found", "Assessment not found")
    ids = list(db.scalars(select(AssessmentQuestion.question_id).where(
        AssessmentQuestion.assessment_id == assessment_id).order_by(AssessmentQuestion.question_id)))
    return {"assessment_id": assessment_id, "question_ids": ids, "selection": "CURATED" if ids else "CONCEPTS"}


def set_pool(db, assessment_id, question_ids):
    db.scalar(select(Assessment).where(Assessment.assessment_id == assessment_id).with_for_update())
    repo = AssessmentRepository(db)
    assessment = repo.get_assessment(assessment_id)
    if assessment is None:
        raise AppError(404, "assessment_not_found", "Assessment not found")
    if assessment.status != "draft" or repo.assessment_session_count(assessment_id):
        raise AppError(409, "assessment_not_editable", "Only an unused draft assessment can change its pool")
    # Clear the old restriction inside this transaction before deriving eligible items.
    db.execute(delete(AssessmentQuestion).where(AssessmentQuestion.assessment_id == assessment_id))
    targets = {t.concept_id: t for t in assessment.targets}
    eligible = {q.question_id for q in repo.eligible_questions(assessment, set())
                if any(tag.confirmed and tag.concept_id in targets
                       and targets[tag.concept_id].min_difficulty <= q.difficulty_level <= targets[tag.concept_id].max_difficulty
                       for tag in q.concept_tags)}
    invalid = sorted(set(question_ids) - eligible)
    if invalid:
        raise AppError(422, "ineligible_pool_questions", "Pool requires validated questions matching the assessment targets",
                       details={"question_ids": invalid})
    db.add_all(AssessmentQuestion(assessment_id=assessment_id, question_id=qid) for qid in question_ids)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "assessment_pool_changed", "The question pool changed concurrently; reload and retry") from None
    return get_pool(db, assessment_id)
