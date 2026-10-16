"""Query-count regressions use PostgreSQL, not repository mocks."""
from contextlib import contextmanager
from sqlalchemy import event

from app.repositories import AccountRepository, AssessmentRepository, CompetencyRepository, QuestionRepository
from app.services.evidence_context import capture_question
from app.services.question_service import _validation_missing
from test_draft_lifecycle import _fixture


@contextmanager
def statements(db):
    seen = []
    def record(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            seen.append(statement)
    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", record)
    try:
        yield seen
    finally:
        event.remove(engine, "before_cursor_execute", record)


def test_auth_roles_and_profile_are_loaded_in_one_query(db_session):
    learner, *_ = _fixture(db_session)
    account_id = learner.account_id
    db_session.expire_all()
    with statements(db_session) as seen:
        loaded = AccountRepository(db_session).get_with_roles(account_id)
        assert loaded.profile.full_name == "Draft Learner"
        assert [r.role_name for r in loaded.roles] == ["Learner"]
    assert len(seen) == 1


def test_snapshot_attempt_reads_do_not_reload_mutable_question_payloads(db_session):
    _, session, attempt, question, _, _, _ = _fixture(db_session)
    sid = session.session_id
    attempt.question_snapshot = capture_question(AssessmentRepository(db_session), question)
    db_session.commit()
    db_session.expire_all()
    with statements(db_session) as seen:
        attempts = AssessmentRepository(db_session).session_attempts(sid)
        assert attempts[0].question_snapshot["prompt"] == "Original prompt"
    assert len(seen) == 1 and "FROM attempt" in seen[0]
    with statements(db_session) as seen:
        evidence = CompetencyRepository(db_session).session_evidence(sid)
        assert evidence == []
    assert len(seen) == 1


def test_eager_sql_bank_validation_does_not_issue_per_question_queries(db_session):
    _, _, _, question, _, _, _ = _fixture(db_session, "sql")
    qid = question.question_id
    db_session.expire_all()
    repo = QuestionRepository(db_session)
    loaded = repo.get_detail(qid)
    with statements(db_session) as seen:
        assert _validation_missing(repo, loaded) == []
    assert seen == []
