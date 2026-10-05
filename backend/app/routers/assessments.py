from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import LearnerOnly
from ..models import Account
from ..schemas import LearnerAssessmentItem, SessionStateResult
from ..services import adaptive_engine, assessment_service

router = APIRouter(prefix="/assessments", tags=["assessment"])


@router.get("", response_model=list[LearnerAssessmentItem])
def list_active_assessments(
    _: Account = LearnerOnly,
    db: Session = Depends(get_db),
):
    """UC12 — the active assessments a learner may start."""
    return assessment_service.list_active_for_learner(db)


@router.post(
    "/{assessment_id}/sessions",
    response_model=SessionStateResult,
    status_code=201,
)
def start_assessment_session(
    assessment_id: int,
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
):
    """UC12 — start (or resume) an adaptive session and serve question 1.

    A second call while a live session exists returns that session's
    current state instead of creating a duplicate.
    """
    return adaptive_engine.start_session(db, assessment_id, learner)
