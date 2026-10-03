from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import LearnerOnly, get_sandbox_runner
from ..models import Account
from ..schemas import AttemptResult, RunSqlRequest, SqlRunResult, SubmitAnswerRequest
from ..services import grading_service, sql_service
from ..services.sandbox_runner import SandboxRunner

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


@router.post("/{session_id}/sql-run", response_model=SqlRunResult)
def run_sql(
    session_id: int,
    payload: RunSqlRequest,
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
    runner: SandboxRunner = Depends(get_sandbox_runner),
):
    """UC13 — run the learner's query in the sandbox on the question's
    primary test dataset. Not graded; submission goes through /answers."""
    return sql_service.run_learner_sql(db, session_id, learner, payload, runner)
