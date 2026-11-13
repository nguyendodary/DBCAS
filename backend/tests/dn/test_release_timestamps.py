"""Release audit times represent transitions, including long grading transactions."""
from sqlalchemy import select, text

from app.models import ResultReleaseEvent
from app.repositories import AssessmentRepository
from app.services.grading_review import transition
from test_draft_lifecycle import _fixture


def test_release_events_use_current_database_time_in_a_long_transaction(db_session):
    _, session, *_ = _fixture(db_session)
    repo = AssessmentRepository(db_session)
    session = repo.lock_session(session.session_id)
    session.status = "completed"
    previous = None
    for status in ["auto_grading", "provisional_ai", "pending_review", "reviewed", "published"]:
        # PostgreSQL now() stays at transaction start; the actual event does not.
        db_session.execute(text("SELECT pg_sleep(0.02)"))
        not_before = repo.server_time()
        transition(db_session, session, status)
        db_session.flush()
        event = db_session.scalar(select(ResultReleaseEvent)
            .where(ResultReleaseEvent.session_id == session.session_id)
            .order_by(ResultReleaseEvent.event_id.desc()).limit(1))
        assert event.created_at >= not_before
        assert previous is None or event.created_at > previous
        assert event.new_status == status
        previous = event.created_at
    assert session.published_at == previous
