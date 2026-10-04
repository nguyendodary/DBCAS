from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import LearnerOnly, get_llm_service, get_sandbox_runner
from ..models import Account
from ..schemas import (
    AttemptResult,
    CompetencyProfileResult,
    RunSqlRequest,
    SqlRunResult,
    SubmitAnswerRequest,
)
from ..services import competency_service, grading_service, sql_service
from ..services.llm import LLMService
from ..services.sandbox_runner import SandboxRunner

router = APIRouter(prefix="/sessions", tags=["assessment"])


@router.post("/{session_id}/answers", response_model=AttemptResult)
def submit_answer(
    session_id: int,
    payload: SubmitAnswerRequest,
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
    runner: SandboxRunner = Depends(get_sandbox_runner),
    llm: LLMService = Depends(get_llm_service),
):
    """UC15/UC16 — submit one answer; graded per the question's format."""
    return grading_service.submit_answer(
        db, session_id, learner, payload, runner, llm
    )


@router.get("/{session_id}/competency", response_model=CompetencyProfileResult)
def get_competency_profile(
    session_id: int,
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
):
    """UC16 — per-concept competency profile of the learner's finalized
    session (recomputed deterministically from stored answer evidence)."""
    return competency_service.session_competency_profile(db, session_id, learner)


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
