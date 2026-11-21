from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import CurrentAccount, LearnerOnly, get_llm_service, get_sandbox_runner
from ..models import Account
from ..repositories import AssessmentRepository
from ..schemas import (
    AttemptResult,
    CompetencyGapResult,
    CompetencyProfileResult,
    EvidenceResult,
    RunSqlRequest,
    ServeResult,
    SessionStateResult,
    SessionSummary,
    SqlRunResult,
    StudyGuidanceResult,
    SubmitAnswerRequest,
    DraftSaveRequest, DraftResult, SubmissionResult,
    CumulativeCompetencyResult,
    ServedQuestion,
    PaperDraftResult, PaperDraftSaveRequest, PaperFlagRequest, PaperFlagResult,
    PaperMetadata, PaperQuestionView, PaperSubmitRequest, PaperSubmitResult,
    PaperTabLeaveRequest, PaperTabLeaveState,
    ReviewRequestCreate, ReviewRequestView, UserReviewRequestView,
)
from ..services import (
    adaptive_engine,
    competency_service,
    grading_service,
    guidance_service,
    session_service,
    sql_service,
    assessment_lifecycle,
    fixed_paper,
)
from ..services.llm import LLMService
from ..services.sandbox_runner import SandboxRunner
from ..schemas_analytics import OwnRank, StatisticsDashboard

router = APIRouter(prefix="/sessions", tags=["assessment"])


@router.get("/statistics", response_model=StatisticsDashboard)
def learner_statistics(learner: Account = LearnerOnly, db: Session = Depends(get_db),
                       assessment_id: int | None = Query(None, ge=1),
                       limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    """Published formal competency, score distribution, progress and topic gaps for this learner."""
    from ..services.statistics_service import dashboard
    return dashboard(db, learner_id=learner.account_id, assessment_id=assessment_id, limit=limit, offset=offset)


@router.get("/ranking", response_model=OwnRank)
def learner_ranking(learner: Account = LearnerOnly, db: Session = Depends(get_db),
                    assessment_id: int | None = Query(None, ge=1)):
    """Own competition rank among published formal evidence; no public roster."""
    from ..services.statistics_service import own_rank
    return own_rank(db, learner.account_id, assessment_id=assessment_id)


@router.get("/competency/cumulative", response_model=CumulativeCompetencyResult)
def cumulative_competency(learner: Account = LearnerOnly, db: Session = Depends(get_db)):
    from ..services.cumulative_competency import profile
    return profile(db, learner.account_id)


@router.post(
    "/{session_id}/review-request", response_model=UserReviewRequestView,
    responses={201: {"model": UserReviewRequestView, "description": "Review request created"}},
)
def create_review_request(
    session_id: int,
    payload: ReviewRequestCreate,
    response: Response,
    idempotency_key: UUID = Header(alias="Idempotency-Key"),
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
):
    """Request one review of the official v1 result (7-day server-clock window).

    ``Idempotency-Key`` is the UUID request key: a replay returns 200 with the
    same case, a new key for an existing case returns 409.
    """
    from ..services import review_flow
    status_code, body = review_flow.request_review(
        db, session_id, learner, idempotency_key, payload.reason
    )
    response.status_code = status_code
    return body


@router.get("/{session_id}/review-request", response_model=UserReviewRequestView | ReviewRequestView)
def get_review_request(
    session_id: int,
    account: Account = CurrentAccount,
    db: Session = Depends(get_db),
):
    """The owner receives the User view. Administrators retain the review case view."""
    from ..services import review_flow
    return review_flow.get_review(db, session_id, account)


@router.put("/{session_id}/draft", response_model=DraftResult)
def save_answer_draft(session_id: int, payload: DraftSaveRequest, learner: Account = LearnerOnly, db: Session = Depends(get_db)):
    """Save an ungraded, revision-controlled draft of the served answer."""
    return assessment_lifecycle.save_draft(db, session_id, learner, payload)


@router.get("/{session_id}/draft", response_model=DraftResult)
def get_answer_draft(session_id: int, question_id: int, learner: Account = LearnerOnly, db: Session = Depends(get_db)):
    return assessment_lifecycle.get_draft(db, session_id, learner, question_id)


@router.get("/{session_id}/paper", response_model=PaperMetadata)
def get_paper(session_id: int, learner: Account = LearnerOnly, db: Session = Depends(get_db)):
    """FIXED only: paper metadata; no prompts, options, keys or scores."""
    return fixed_paper.paper_metadata(db, session_id, learner)


@router.post("/{session_id}/paper/submit", response_model=PaperSubmitResult)
def submit_paper(session_id: int, payload: PaperSubmitRequest | None = None, learner: Account = LearnerOnly,
                 db: Session = Depends(get_db)):
    """FIXED only: finalize the whole paper once; later calls return the summary."""
    return fixed_paper.final_submit(db, session_id, learner, payload or PaperSubmitRequest())


@router.post("/{session_id}/paper/tab-leave", response_model=PaperTabLeaveState)
def report_paper_tab_leave(session_id: int, payload: PaperTabLeaveRequest,
                           learner: Account = LearnerOnly, db: Session = Depends(get_db)):
    """FIXED only: report focus leave/return; the server owns the counter."""
    return fixed_paper.report_tab_leave(db, session_id, learner, payload)


@router.get("/{session_id}/paper/{seq_no}", response_model=PaperQuestionView)
def get_paper_question(session_id: int, seq_no: int, learner: Account = LearnerOnly, db: Session = Depends(get_db)):
    """FIXED only: sanitized question and saved draft; records the first open."""
    return fixed_paper.paper_question(db, session_id, seq_no, learner)


@router.put("/{session_id}/paper/{seq_no}/draft", response_model=PaperDraftResult)
def save_paper_draft(session_id: int, seq_no: int, payload: PaperDraftSaveRequest, learner: Account = LearnerOnly,
                     db: Session = Depends(get_db)):
    """FIXED only: save an ungraded, revision-controlled draft by seq."""
    return fixed_paper.save_draft(db, session_id, seq_no, learner, payload)


@router.put("/{session_id}/paper/{seq_no}/flag", response_model=PaperFlagResult)
def set_paper_flag(session_id: int, seq_no: int, payload: PaperFlagRequest, learner: Account = LearnerOnly,
                   db: Session = Depends(get_db)):
    """FIXED only: flag a question with its own optimistic revision."""
    return fixed_paper.set_flag(db, session_id, seq_no, learner, payload)


@router.post("/{session_id}/submit", response_model=SubmissionResult)
def submit_and_advance(session_id: int, payload: SubmitAnswerRequest, learner: Account = LearnerOnly,
                       db: Session = Depends(get_db), runner: SandboxRunner = Depends(get_sandbox_runner), llm: LLMService = Depends(get_llm_service)):
    """Commit the answer and authoritative next state together; retry is safe."""
    from ..config import get_settings
    if get_settings().auto_grade_essays and llm.is_configured():
        llm = None  # The local maintenance worker grades the durable essay job.
    answer = assessment_lifecycle.submit(db, session_id, learner, payload, runner, llm)
    session = AssessmentRepository(db).get_session(session_id)
    if session.status == "in_progress":
        if adaptive_engine._expired(session, AssessmentRepository(db).server_time()):
            assessment_lifecycle.finalize(db, session, timed_out=True)
        else:
            adaptive_engine.serve_next(db, session_id, learner, commit=False)
    db.commit()
    return SubmissionResult(answer=answer, state=adaptive_engine.get_state(db, session_id, learner))


@router.get("", response_model=list[SessionSummary])
def list_sessions(
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
):
    """UC18 — the learner's own sessions, newest first (history/pickers)."""
    return session_service.list_learner_sessions(db, learner)


@router.get("/{session_id}", response_model=SessionStateResult)
def get_session_state(
    session_id: int,
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
    display_locale: Literal["en", "vi"] | None = None,
):
    """UC12 — live session state: status, countdown, progress, and the
    currently served (unanswered) question, sanitized for the exam UI.
    An elapsed in-progress session is flipped to timed_out."""
    return adaptive_engine.get_state(db, session_id, learner, display_locale=display_locale)


@router.get("/{session_id}/questions", response_model=list[ServedQuestion])
def get_served_questions(
    session_id: int,
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
    display_locale: Literal["en", "vi"] | None = None,
):
    """Browse delivered questions and own saved answers without grading keys."""
    return adaptive_engine.served_questions(db, session_id, learner, display_locale)


@router.post("/{session_id}/serve-next", response_model=ServeResult)
def serve_next_question(
    session_id: int,
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
):
    """UC12/FR-15 — return the pending question or adaptively serve the
    next one; every new serve is audited in selection_log."""
    return adaptive_engine.serve_next(db, session_id, learner)


@router.post("/{session_id}/finish", response_model=SessionStateResult)
def finish_session(
    session_id: int,
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
):
    """UC12 — the learner submits the session. Finalizes to completed (or
    timed_out once the window elapsed) and recomputes competency + gaps
    deterministically. Served-but-unanswered questions count as no
    evidence."""
    return adaptive_engine.finish_session(db, session_id, learner)


@router.get("/{session_id}/evidence", response_model=EvidenceResult)
def get_session_evidence(
    session_id: int,
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
    display_locale: Literal["en", "vi"] | None = None,
):
    """UC18 — per-question evidence for review: type, concepts, difficulty,
    the learner's submitted answer, and the grading result. Finalized
    sessions only; correct answers are revealed only after submission."""
    return adaptive_engine.get_evidence(db, session_id, learner, display_locale=display_locale)


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


@router.get("/{session_id}/gaps", response_model=CompetencyGapResult)
def get_gap_report(
    session_id: int,
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
):
    """UC17 — competency gaps ranked by shortfall (the 'What to study next'
    list); explanations are filled in via the assistive LLM when configured
    and never affect scores or order."""
    return competency_service.session_gap_report(db, session_id, learner, llm)


@router.get("/{session_id}/guidance", response_model=StudyGuidanceResult)
def get_study_guidance(
    session_id: int,
    include_explanations: bool = True,
    learner: Account = LearnerOnly,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
):
    """UC17 refinement — the ranked 'What to study next' guidance: gap
    concepts ordered by shortfall descending. The skill graph describes
    readiness; LLM explanations never affect priority."""
    return guidance_service.session_study_guidance(
        db, session_id, learner, llm if include_explanations else None
    )


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
    from ..services.sandbox_diagnostics import operation
    with operation(runner, "user_sql_run"):
        return sql_service.run_learner_sql(db, session_id, learner, payload, runner)
