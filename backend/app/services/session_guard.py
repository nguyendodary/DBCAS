"""Shared guards for session-scoped learner operations.

Used by both answer submission (grading) and ad-hoc SQL execution, so the
ownership, session-state, expiry, and served-question rules stay identical.
"""

from datetime import datetime, timezone

from ..errors import AppError
from ..models import Account, AssessmentSession, Attempt
from ..repositories import AssessmentRepository


def load_owned_active_session(
    repo: AssessmentRepository, session_id: int, learner: Account
) -> AssessmentSession:
    """Load a session that belongs to the learner and is still writable.

    Other learners' sessions answer 404 (existence is not leaked). Expired
    sessions are flipped to ``timed_out`` once, then rejected with 409.
    """
    session = repo.get_session(session_id)
    if session is None or session.learner_id != learner.account_id:
        raise AppError(404, "session_not_found", "Assessment session not found")
    if session.status != "in_progress":
        raise AppError(409, "session_not_active", "Session is no longer in progress")
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        session.status = "timed_out"
        repo.db.commit()
        raise AppError(409, "session_expired", "Session time has expired")
    return session


def load_owned_finalized_session(
    repo: AssessmentRepository, session_id: int, learner: Account
) -> AssessmentSession:
    """Load a session that belongs to the learner and has ended.

    Same ownership/404 rule as the write path — other learners' sessions
    answer 404 so their existence is not leaked.
    """
    session = repo.get_session(session_id)
    if session is None or session.learner_id != learner.account_id:
        raise AppError(404, "session_not_found", "Assessment session not found")
    return ensure_session_finalized(session, repo.db)


def load_finalized_session(
    repo: AssessmentRepository, session_id: int
) -> AssessmentSession:
    """Load any session that has ended — the admin-scoped read path."""
    session = repo.get_session(session_id)
    if session is None:
        raise AppError(404, "session_not_found", "Assessment session not found")
    return ensure_session_finalized(session, repo.db)


def ensure_session_finalized(
    session: AssessmentSession, db
) -> AssessmentSession:
    """An in-progress session past ``expires_at`` is finalized to
    ``timed_out`` once (auto-submit at 00:00) so results become readable;
    a still-running session conflicts with 409.
    """
    if session.status == "in_progress":
        now = datetime.now(timezone.utc)
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            session.status = "timed_out"
            db.commit()
        else:
            raise AppError(
                409, "session_not_finalized", "Assessment session is still running"
            )
    return session


def load_served_attempt(
    repo: AssessmentRepository, session_id: int, question_id: int
) -> Attempt:
    """Load the attempt created when the question was served in this session."""
    attempt = repo.get_attempt(session_id, question_id)
    if attempt is None:
        raise AppError(
            404, "question_not_served", "This question was not served in the session"
        )
    return attempt
