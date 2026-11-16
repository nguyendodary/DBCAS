"""FIXED paper endpoints: free navigation, revision-controlled drafts and
flags, and one final grading transaction. Gated by ``runner_mode == "fixed"``;
legacy and adaptive sessions keep their existing per-answer endpoints.
"""
from datetime import timezone

from ..errors import AppError
from ..repositories import AssessmentRepository
from ..schemas import (
    PaperDraftResult,
    PaperDraftSaveRequest,
    PaperFlagRequest,
    PaperFlagResult,
    PaperMetadata,
    PaperOption,
    PaperQuestionMeta,
    PaperQuestionView,
    PaperSubmitRequest,
    PaperSubmitResult,
)
from .assessment_lifecycle import (
    _answer_dict,
    _expired,
    _snapshot,
    finalize,
)
from .evidence_context import question_view


def _fixed_session(db, session_id, learner):
    """Ownership and mode guard; a non-fixed session never reaches paper logic."""
    repo = AssessmentRepository(db)
    session = repo.lock_session(session_id)
    if session is None or session.learner_id != learner.account_id:
        raise AppError(404, "session_not_found", "Assessment session not found")
    if (session.config_snapshot or {}).get("runner_mode") != "fixed":
        raise AppError(409, "paper_mode_unavailable",
                       "This session does not use fixed paper mode")
    return repo, session


def _active(repo, session):
    """Paper reads/writes require an active, unexpired session.

    A past deadline always answers ``session_expired`` (finalizing once if the
    session is still live), even when a previous request already timed it out.
    """
    now = repo.server_time()
    if _expired(session, now):
        if session.status == "in_progress":
            finalize(repo.db, session, timed_out=True)
        raise AppError(409, "session_expired", "Session time has expired")
    if session.status != "in_progress":
        raise AppError(409, "session_not_active", "Session is no longer in progress")


def _clock(repo, session):
    now = repo.server_time()
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return now, max(0, int((expires_at - now).total_seconds()))


def _attempt(repo, session, seq_no):
    attempt = repo.get_attempt_by_seq(session.session_id, seq_no)
    if attempt is None:
        raise AppError(404, "question_not_in_paper",
                       "This question is not part of the paper")
    return attempt


def _has_answer(attempt) -> bool:
    draft = attempt.draft_answer or {}
    return any(value is not None and (not isinstance(value, str) or value.strip())
               for value in draft.values())


def _question_type(attempt) -> str:
    snapshot = attempt.question_snapshot or {}
    return snapshot.get("question_type") or (
        attempt.question.question_type if attempt.question else ""
    )


def paper_metadata(db, session_id, learner) -> PaperMetadata:
    """Palette metadata for the whole paper — never prompts, options or keys."""
    repo, session = _fixed_session(db, session_id, learner)
    _active(repo, session)
    now, remaining = _clock(repo, session)
    attempts = repo.session_attempts(session.session_id)
    questions = [
        PaperQuestionMeta(
            seq_no=a.seq_no,
            question_id=a.question_id,
            question_type=_question_type(a),
            answered=_has_answer(a),
            flagged=bool(a.is_flagged),
            opened=a.first_opened_at is not None,
            draft_revision=a.draft_revision,
        )
        for a in attempts
    ]
    opened = [a for a in attempts if a.first_opened_at is not None]
    last = max(opened, key=lambda a: a.first_opened_at) if opened else None
    snapshot = session.config_snapshot or {}
    started_at = session.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return PaperMetadata(
        session_id=session.session_id,
        status=session.status,
        assessment_title=snapshot.get("title") or "Assessment",
        started_at=started_at,
        expires_at=expires_at,
        server_now=now,
        remaining_seconds=remaining,
        question_count=len(attempts),
        answered_count=sum(q.answered for q in questions),
        flagged_count=sum(q.flagged for q in questions),
        last_opened_seq=last.seq_no if last else None,
        questions=questions,
    )


def paper_question(db, session_id, seq_no, learner) -> PaperQuestionView:
    """Sanitized content for one seq; records first_opened_at on first open."""
    repo, session = _fixed_session(db, session_id, learner)
    _active(repo, session)
    attempt = _attempt(repo, session, seq_no)
    question = _snapshot(repo, attempt)
    view = question_view(attempt, session.locale or "en")
    now, remaining = _clock(repo, session)
    options = [
        PaperOption(option_id=o.option_id, option_label=o.option_label,
                    option_text=o.option_text)
        for o in view.options
    ] if question.question_type == "mcq" else []
    schema_sql = None
    if question.question_type == "sql":
        dataset = next((d for d in (view.datasets or []) if not d.is_edge_case), None)
        schema_sql = getattr(dataset, "setup_sql", None) if dataset else None
    if attempt.first_opened_at is None:
        attempt.first_opened_at = now
        db.commit()
    return PaperQuestionView(
        seq_no=attempt.seq_no,
        question_id=attempt.question_id,
        question_type=question.question_type,
        content_locale=getattr(view, "content_locale", "en"),
        prompt=view.prompt,
        options=options,
        schema_sql=schema_sql,
        draft=attempt.draft_answer,
        draft_revision=attempt.draft_revision,
        answered=_has_answer(attempt),
        flagged=bool(attempt.is_flagged),
        flag_revision=attempt.flag_revision,
        first_opened_at=attempt.first_opened_at,
        remaining_seconds=remaining,
        server_now=now,
    )


def save_draft(db, session_id, seq_no, learner, payload: PaperDraftSaveRequest) -> PaperDraftResult:
    """Reuse the legacy answer validation and revision chain; never grades."""
    repo, session = _fixed_session(db, session_id, learner)
    _active(repo, session)
    attempt = _attempt(repo, session, seq_no)
    if attempt.submitted_at is not None:
        raise AppError(409, "already_submitted", "This question was already submitted")
    answer = _answer_dict(payload, _snapshot(repo, attempt))
    if payload.revision == attempt.draft_revision and answer == attempt.draft_answer:
        return PaperDraftResult(seq_no=seq_no, revision=attempt.draft_revision,
                                saved_at=attempt.draft_saved_at, answered=_has_answer(attempt))
    if payload.revision != attempt.draft_revision + 1:
        raise AppError(409, "draft_revision_conflict",
                       "A newer saved draft exists. Reload it before saving.",
                       details={"revision": attempt.draft_revision})
    attempt.draft_answer = answer
    attempt.draft_revision = payload.revision
    attempt.draft_saved_at = repo.server_time()
    db.commit()
    return PaperDraftResult(seq_no=seq_no, revision=attempt.draft_revision,
                            saved_at=attempt.draft_saved_at, answered=_has_answer(attempt))


def set_flag(db, session_id, seq_no, learner, payload: PaperFlagRequest) -> PaperFlagResult:
    """Flags are independent of answers and use their own optimistic revision."""
    repo, session = _fixed_session(db, session_id, learner)
    _active(repo, session)
    attempt = _attempt(repo, session, seq_no)
    if payload.revision != attempt.flag_revision:
        raise AppError(409, "flag_revision_conflict",
                       "A newer flag exists. Reload it before saving.",
                       details={"revision": attempt.flag_revision})
    attempt.is_flagged = payload.flagged
    attempt.flag_revision = payload.revision + 1
    db.commit()
    return PaperFlagResult(seq_no=seq_no, flagged=attempt.is_flagged,
                           revision=attempt.flag_revision)


def _summary(repo, session) -> PaperSubmitResult:
    attempts = repo.session_attempts(session.session_id)
    answered = sum(_has_answer(a) for a in attempts)
    return PaperSubmitResult(
        status=session.status,
        submitted_at=session.submitted_at,
        answered_count=answered,
        unanswered_count=len(attempts) - answered,
        flagged_count=sum(1 for a in attempts if a.is_flagged),
        final=True,
        next=f"/evaluations/{session.session_id}",
    )


def final_submit(db, session_id, learner, payload: PaperSubmitRequest) -> PaperSubmitResult:
    """Idempotent: an already-finalized paper returns its summary, never re-grades."""
    repo, session = _fixed_session(db, session_id, learner)
    if session.status != "in_progress":
        return _summary(repo, session)
    timed_out = _expired(session, repo.server_time())
    # The existing finalize path grades saved drafts, zeroes unanswered items,
    # reconciles release state and commits everything in one transaction.
    finalized = finalize(db, session, timed_out=timed_out)
    return _summary(repo, finalized)
