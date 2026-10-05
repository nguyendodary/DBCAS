from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import LearnerOnly
from ..models import Account
from ..schemas import LearnerAssessmentItem
from ..services import assessment_service

router = APIRouter(prefix="/assessments", tags=["assessment"])


@router.get("", response_model=list[LearnerAssessmentItem])
def list_active_assessments(
    _: Account = LearnerOnly,
    db: Session = Depends(get_db),
):
    """UC12 — the active assessments a learner may start."""
    return assessment_service.list_active_for_learner(db)
