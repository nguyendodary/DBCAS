from datetime import datetime, timezone
from types import SimpleNamespace as Row
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.errors import AppError
from app.schemas import FinishSessionRequest
from app.services import adaptive_engine, assessment_lifecycle


@pytest.mark.parametrize('policy', ['IMMEDIATE', 'HUMAN_VERIFIED'])
def test_choice_applied_before_finalization(monkeypatch, policy):
    session = Row(learner_id=7, status='in_progress', result_release_policy='IMMEDIATE', release_policy_chosen_at=None)
    now = datetime.now(timezone.utc)
    repo = Row(lock_session=lambda _: session, server_time=lambda: now)
    monkeypatch.setattr(adaptive_engine, 'AssessmentRepository', lambda _: repo)
    monkeypatch.setattr(adaptive_engine, '_state', lambda *_: session)
    finalized = []
    monkeypatch.setattr(assessment_lifecycle, 'finalize', lambda db, s: finalized.append((s.result_release_policy, s.release_policy_chosen_at)))
    db = Mock()
    adaptive_engine.finish_session(db, 1, Row(account_id=7), result_release_policy=policy)
    assert finalized == [(policy, now)]
    db.flush.assert_called_once()


def test_cannot_change_choice_after_submission(monkeypatch):
    session = Row(learner_id=7, status='completed', result_release_policy='HUMAN_VERIFIED', release_policy_chosen_at=datetime.now(timezone.utc))
    monkeypatch.setattr(adaptive_engine, 'AssessmentRepository', lambda _: Row(lock_session=lambda _: session))
    with pytest.raises(AppError) as error:
        adaptive_engine.finish_session(Mock(), 1, Row(account_id=7), result_release_policy='IMMEDIATE')
    assert error.value.code == 'release_choice_locked'


def test_cannot_choose_for_another_learner(monkeypatch):
    monkeypatch.setattr(adaptive_engine, 'AssessmentRepository', lambda _: Row(lock_session=lambda _: Row(learner_id=99)))
    with pytest.raises(AppError) as error:
        adaptive_engine.finish_session(Mock(), 1, Row(account_id=7), result_release_policy='IMMEDIATE')
    assert error.value.status_code == 404


def test_finish_retry_keeps_original_choice(monkeypatch):
    session = Row(learner_id=7, status='completed', result_release_policy='HUMAN_VERIFIED')
    monkeypatch.setattr(adaptive_engine, 'AssessmentRepository', lambda _: Row(lock_session=lambda _: session))
    monkeypatch.setattr(adaptive_engine, '_state', lambda *_: session)
    monkeypatch.setattr(assessment_lifecycle, 'finalize', lambda *_: None)
    db = Mock()
    assert adaptive_engine.finish_session(db, 1, Row(account_id=7), result_release_policy='HUMAN_VERIFIED') is session
    db.flush.assert_not_called()


def test_invalid_policy_rejected():
    with pytest.raises(ValidationError):
        FinishSessionRequest(result_release_policy='anything')


@pytest.mark.parametrize('policy,expected', [('IMMEDIATE', 'published'), ('HUMAN_VERIFIED', 'pending_review')])
def test_release_boundary_honors_learner_choice(monkeypatch, policy, expected):
    from app.services import grading_review
    session = Row(status='completed', release_status='unsubmitted', result_release_policy=policy, session_id=1)
    attempts = [Row(attempt_id=1, submitted_at=datetime.now(timezone.utc), grading_status='graded', score=1)]
    monkeypatch.setattr(grading_review, 'AssessmentRepository', lambda _: Row(session_attempts=lambda _: attempts))
    monkeypatch.setattr(grading_review, 'question_view', lambda _: Row(question_type='essay'))
    status = []
    monkeypatch.setattr(grading_review, 'transition', lambda db, s, value, **kwargs: status.append(value))
    db = Mock()
    db.scalars.return_value = []
    grading_review.reconcile(db, session)
    assert status == [expected]


def test_migration_guards_choice_in_isolated_schema():
    """Use a temporary schema and roll back all DDL and data; never touch app rows."""
    import uuid
    import psycopg
    from psycopg import sql
    from app.config import get_settings, ROOT_DIR
    url = get_settings().database_url.replace('postgresql+psycopg://', 'postgresql://', 1)
    with psycopg.connect(url) as conn:
        try:
            namespace = 'release_choice_test_' + uuid.uuid4().hex[:12]
            conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(namespace)))
            conn.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(namespace)))
            conn.execute("CREATE TABLE assessment_session (session_id INT PRIMARY KEY, status TEXT, release_status TEXT, result_release_policy TEXT, start_request_id TEXT)")
            conn.execute((ROOT_DIR / 'db/migrations/013_learner_release_choice.sql').read_text(encoding='utf-8'), prepare=False)
            conn.execute('CREATE TRIGGER policy_guard BEFORE UPDATE ON assessment_session FOR EACH ROW EXECUTE FUNCTION preserve_session_release_policy()')
            conn.execute("INSERT INTO assessment_session VALUES (1,'in_progress','unsubmitted','IMMEDIATE','request-1',NULL),(2,'completed','published','IMMEDIATE','request-2',NULL)")
            conn.execute("UPDATE assessment_session SET result_release_policy='HUMAN_VERIFIED',release_policy_chosen_at=now() WHERE session_id=1")
            conn.execute("UPDATE assessment_session SET status='completed',release_status='pending_review' WHERE session_id=1")
            for statement in [
                "UPDATE assessment_session SET result_release_policy='IMMEDIATE' WHERE session_id=1",
                "UPDATE assessment_session SET release_policy_chosen_at=NULL WHERE session_id=1",
                "UPDATE assessment_session SET start_request_id='changed' WHERE session_id=1",
                "UPDATE assessment_session SET result_release_policy='HUMAN_VERIFIED',release_policy_chosen_at=now() WHERE session_id=2",
            ]:
                with pytest.raises(psycopg.errors.RaiseException):
                    with conn.transaction():
                        conn.execute(statement)
            assert conn.execute('SELECT result_release_policy FROM assessment_session WHERE session_id=1').fetchone()[0] == 'HUMAN_VERIFIED'
        finally:
            conn.rollback()
