from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import LearnerOnly
from ..models import Account
from ..schemas import AttemptResult, SubmitAnswerRequest
from ..services import grading_service

router = APIRouter(prefix="/sessions", tags=["assessment"])


@router.post("/{session_id}/answers", response_model=AttemptResult)
def submit_answer(
    session_id: int,
    payload: SubmitAnswerRequest,
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
):
    """UC15/UC16 — submit one answer; MCQ answers are graded by answer key."""
    return grading_service.submit_answer(db, session_id, learner, payload)
