"""Assessment session use cases — learner-facing lifecycle and history.

Currently: UC18's own-session list. The adaptive serve/finish engine grows
here under FR-15.
"""

from sqlalchemy.orm import Session

from ..models import Account
from ..repositories import AssessmentRepository
from ..schemas import SessionSummary


def list_learner_sessions(db: Session, learner: Account) -> list[SessionSummary]:
    """UC18 — the learner's sessions, newest first, with attempt counts."""
    repo = AssessmentRepository(db)
    sessions = repo.sessions_for_learner(learner.account_id)
    counts = repo.attempt_counts([s.session_id for s in sessions])
    items = []
    for s in sessions:
        served, answered = counts.get(s.session_id, (0, 0))
        items.append(
            SessionSummary(
                session_id=s.session_id,
                assessment_id=s.assessment_id,
                assessment_title=s.assessment.title if s.assessment else "",
                status=s.status,
                started_at=s.started_at,
                expires_at=s.expires_at,
                submitted_at=s.submitted_at,
                served_count=served,
                answered_count=answered,
            )
        )
    return items
