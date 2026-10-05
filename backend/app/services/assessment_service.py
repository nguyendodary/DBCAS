"""Adaptive assessment configuration — UC09 / Admin story 7.

An assessment is a configuration (target concepts with difficulty ranges
and per-concept passing benchmarks), never a fixed question set — the
adaptive engine picks validated items at run time. Session defaults per
the spec: at most 13 questions, a 60-minute countdown, and a target mix
of 10 MCQ / 2 SQL / 1 essay.

Lifecycle: draft -> active (learners may start it) -> closed. Content is
editable only while draft; activating requires at least one target
concept (doc A1) and the target-mix sum must fit within max_questions
(the DB CHECK enforces the same bound).
"""

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import Account, Assessment
from ..repositories import AssessmentRepository, CurriculumRepository
from ..schemas import (
    AssessmentConceptResult,
    AssessmentDetail,
    AssessmentListItem,
    AssessmentUpsertRequest,
    LearnerAssessmentItem,
)


def _to_list_item(
    repo: AssessmentRepository,
    a: Assessment,
    session_count: Optional[int] = None,
) -> AssessmentListItem:
    return AssessmentListItem(
        assessment_id=a.assessment_id,
        title=a.title,
        status=a.status,
        max_questions=a.max_questions,
        duration_min=a.duration_min,
        created_at=a.created_at,
        target_count=len(a.targets),
        session_count=(
            session_count
            if session_count is not None
            else repo.assessment_session_count(a.assessment_id)
        ),
    )


def _to_detail(repo: AssessmentRepository, a: Assessment) -> AssessmentDetail:
    return AssessmentDetail(
        **_to_list_item(repo, a).model_dump(),
        description=a.description,
        target_mcq=a.target_mcq,
        target_sql=a.target_sql,
        target_essay=a.target_essay,
        concepts=[
            AssessmentConceptResult(
                concept_id=t.concept_id,
                concept_code=t.concept.concept_code,
                concept_name=t.concept.concept_name,
                subject_area=t.concept.subject_area,
                min_difficulty=t.min_difficulty,
                max_difficulty=t.max_difficulty,
                target_pct=t.target_pct,
            )
            for t in sorted(a.targets, key=lambda t: t.concept_id)
        ],
    )


def _require_assessment(
    repo: AssessmentRepository, assessment_id: int
) -> Assessment:
    a = repo.get_assessment(assessment_id)
    if a is None:
        raise AppError(404, "assessment_not_found", "Assessment not found")
    return a


def _check_payload(db: Session, payload: AssessmentUpsertRequest) -> None:
    if payload.target_mcq + payload.target_sql + payload.target_essay > (
        payload.max_questions
    ):
        raise AppError(
            422,
            "target_mix_too_large",
            "target_mcq + target_sql + target_essay must not exceed max_questions",
        )
    ids = [c.concept_id for c in payload.concepts]
    if len(set(ids)) != len(ids):
        raise AppError(422, "duplicate_concept_ids", "Concept ids must be unique")
    found = {c.concept_id for c in CurriculumRepository(db).get_concepts(set(ids))}
    missing = set(ids) - found
    if missing:
        raise AppError(
            404,
            "concept_not_found",
            "Unknown concept ids",
            details=[{"concept_id": i} for i in sorted(missing)],
        )


def _apply_targets(
    repo: AssessmentRepository, a: Assessment, payload: AssessmentUpsertRequest
) -> None:
    for c in payload.concepts:
        repo.upsert_target(
            a.assessment_id,
            c.concept_id,
            min_d=c.min_difficulty,
            max_d=c.max_difficulty,
            target_pct=c.target_pct,
        )
    repo.replace_targets(a, {c.concept_id for c in payload.concepts})


# ---------- admin ----------


def list_assessments(db: Session) -> list[AssessmentListItem]:
    repo = AssessmentRepository(db)
    counts = repo.session_counts()
    return [
        _to_list_item(repo, a, counts.get(a.assessment_id, 0))
        for a in repo.list_assessments()
    ]


def get_assessment(db: Session, assessment_id: int) -> AssessmentDetail:
    repo = AssessmentRepository(db)
    return _to_detail(repo, _require_assessment(repo, assessment_id))


def create_assessment(
    db: Session, payload: AssessmentUpsertRequest, admin: Account
) -> AssessmentDetail:
    _check_payload(db, payload)
    repo = AssessmentRepository(db)
    try:
        a = repo.create_assessment(
            title=payload.title.strip(),
            description=payload.description,
            max_questions=payload.max_questions,
            duration_min=payload.duration_min,
            target_mcq=payload.target_mcq,
            target_sql=payload.target_sql,
            target_essay=payload.target_essay,
            status="draft",
            created_by=admin.account_id,
        )
        _apply_targets(repo, a, payload)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(422, "invalid_assessment", "Assessment violates a constraint")
    db.expire(a)
    return _to_detail(repo, repo.get_assessment(a.assessment_id))


def replace_assessment(
    db: Session, assessment_id: int, payload: AssessmentUpsertRequest
) -> AssessmentDetail:
    repo = AssessmentRepository(db)
    a = _require_assessment(repo, assessment_id)
    if a.status != "draft":
        raise AppError(
            409,
            "assessment_not_draft",
            "Only draft assessments can be edited; close it and draft a new version",
        )
    _check_payload(db, payload)
    try:
        a.title = payload.title.strip()
        a.description = payload.description
        a.max_questions = payload.max_questions
        a.duration_min = payload.duration_min
        a.target_mcq = payload.target_mcq
        a.target_sql = payload.target_sql
        a.target_essay = payload.target_essay
        _apply_targets(repo, a, payload)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(422, "invalid_assessment", "Assessment violates a constraint")
    db.expire(a)
    return _to_detail(repo, repo.get_assessment(assessment_id))


_TRANSITIONS = {
    ("draft", "active"),
    ("active", "closed"),
    ("closed", "draft"),
}


def set_assessment_status(
    db: Session, assessment_id: int, status: str
) -> AssessmentDetail:
    """draft -> active -> closed (-> draft). Activating requires at least
    one target concept (documented invalid-configuration case A1)."""
    repo = AssessmentRepository(db)
    a = _require_assessment(repo, assessment_id)
    if (a.status, status) not in _TRANSITIONS:
        raise AppError(
            409,
            "invalid_status_transition",
            f"Cannot move assessment from '{a.status}' to '{status}'",
        )
    if status == "active" and not a.targets:
        raise AppError(
            422,
            "no_target_concepts",
            "Assessment needs at least one target concept before activation",
        )
    a.status = status
    db.commit()
    db.expire(a)
    return _to_detail(repo, repo.get_assessment(assessment_id))


def delete_assessment(db: Session, assessment_id: int) -> None:
    repo = AssessmentRepository(db)
    a = _require_assessment(repo, assessment_id)
    if repo.assessment_session_count(assessment_id):
        raise AppError(
            409,
            "assessment_in_use",
            "Assessment has sessions and cannot be deleted",
        )
    for t in list(a.targets):
        db.delete(t)
    db.delete(a)
    db.commit()


# ---------- learner ----------


def list_active_for_learner(db: Session) -> list[LearnerAssessmentItem]:
    return [
        LearnerAssessmentItem(
            assessment_id=a.assessment_id,
            title=a.title,
            description=a.description,
            duration_min=a.duration_min,
            max_questions=a.max_questions,
            concept_count=len(a.targets),
        )
        for a in AssessmentRepository(db).list_active_assessments()
    ]
