"""Publication choices and post-publication review; no database fixtures."""
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest

from app.errors import AppError
from app.schemas import GradeReviewRequest
from app.services import adaptive_engine, grading_review, competency_service


def test_human_mode_requires_essay_review_but_not_sql_review(monkeypatch):
    attempts = [NS(attempt_id=1, submitted_at=True, score=1, grading_status="graded", kind="sql"),
                NS(attempt_id=2, submitted_at=True, score=1, grading_status="graded", kind="essay")]
    repo = Mock()
    repo.session_attempts.return_value = attempts
    monkeypatch.setattr(grading_review, "AssessmentRepository", lambda _: repo)
    monkeypatch.setattr(grading_review, "question_view", lambda a: NS(question_type=a.kind))
    session = NS(session_id=1, status="completed", release_status="pending_review", result_release_policy="HUMAN_VERIFIED", review_revision=0)
    db = Mock()
    db.scalars.return_value = []
    grading_review.reconcile(db, session)
    assert session.release_status == "pending_review"
    db.scalars.return_value = [2]
    grading_review.reconcile(db, session)
    assert session.release_status == "reviewed"
    with pytest.raises(AppError):
        grading_review.require_published(session)


@pytest.mark.parametrize('before_publication', [False, True])
def test_immediate_score_publishes_then_admin_can_review_with_original_grade_audited(monkeypatch, before_publication):
    session = NS(session_id=1, learner_id=2, status="completed", release_status="auto_grading", result_release_policy="IMMEDIATE", review_revision=0)
    attempt = NS(attempt_id=3, submitted_at=True, score=Decimal("0.5"), grading_status="graded", review_revision=0,
                 grading_detail={"grader": "ai", "feedback": "Original"})
    repo, db = Mock(), Mock()
    repo.session_attempts.return_value = [attempt]
    repo.server_time.return_value = datetime.now(timezone.utc)
    monkeypatch.setattr(grading_review, "AssessmentRepository", lambda _: repo)
    monkeypatch.setattr(grading_review, "_session", lambda *args: session)
    monkeypatch.setattr(grading_review, "question_view", lambda _: NS(points=Decimal("1"), question_type="essay"))
    monkeypatch.setattr(grading_review, "detail", lambda *args: {"published": session.release_status == "published"})
    monkeypatch.setattr(competency_service, "detect_session_gaps", Mock())
    if not before_publication:
        grading_review.reconcile(db, session)
        assert session.release_status == "published"
    db.scalar.return_value = None
    result = grading_review.approve(db, 1, 3, GradeReviewRequest(revision=0, score="0.75", comments="Reviewed feedback"), NS(account_id=4))
    assert result == {"published": True}
    assert attempt.score == Decimal("0.75")
    assert attempt.grading_detail["reviewer_comments"] == "Reviewed feedback"
    review = next(call.args[0] for call in db.add.call_args_list if hasattr(call.args[0], "automated_score"))
    assert review.automated_score == Decimal("0.5")
    assert review.automated_detail == {"grader": "ai", "feedback": "Original"}


def test_review_queue_includes_submitted_immediate_awaiting_grading(monkeypatch):
    from sqlalchemy import create_engine, text
    from app.models import AssessmentSession
    engine = create_engine('sqlite://')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE assessment_session (session_id INTEGER, status TEXT, result_release_policy TEXT, release_status TEXT, submitted_at TEXT)'))
        connection.execute(text('CREATE TABLE attempt (attempt_id INTEGER, session_id INTEGER, submitted_at TEXT, question_id INTEGER, question_snapshot JSON)'))
        connection.execute(text('CREATE TABLE question (question_id INTEGER, question_type TEXT)'))
        connection.execute(text("INSERT INTO question VALUES (1, 'essay'), (2, 'sql'), (3, 'mcq')"))
        connection.execute(text('CREATE TABLE grade_review (attempt_id INTEGER)'))
        for sid, status, policy, release in [
            (1, 'completed', 'IMMEDIATE', 'auto_grading'),
            (2, 'completed', 'IMMEDIATE', 'published'),
            (3, 'completed', 'IMMEDIATE', 'published'),
            (4, 'in_progress', 'IMMEDIATE', 'auto_grading'),
            (5, 'completed', 'HUMAN_VERIFIED', 'pending_review'),
            (6, 'completed', 'HUMAN_VERIFIED', 'published'),
            (7, 'completed', 'IMMEDIATE', 'auto_grading'),
            (8, 'completed', 'HUMAN_VERIFIED', 'grading_failed'),
        ]:
            connection.execute(text('INSERT INTO assessment_session VALUES (:sid,:status,:policy,:release,"2026-10-25")'), dict(sid=sid,status=status,policy=policy,release=release))
            question_id = 2 if sid == 7 else 3 if sid == 8 else 1
            connection.execute(text('INSERT INTO attempt VALUES (:sid,:sid,"2026-10-25",:qid,NULL)'), dict(sid=sid, qid=question_id))
        connection.execute(text('INSERT INTO grade_review VALUES (3)'))
        db = NS(scalars=lambda query: connection.scalars(query.with_only_columns(AssessmentSession.session_id)))
        monkeypatch.setattr(grading_review, '_summary', lambda db, sid: sid)
        assert grading_review.list_pending(db) == [1, 2, 5]
    engine.dispose()


@pytest.mark.parametrize('kind', ['mcq', 'sql'])
def test_administrator_cannot_change_automated_nonessay_scores(monkeypatch, kind):
    session = NS(session_id=1, learner_id=2, status='completed', result_release_policy='IMMEDIATE')
    attempt = NS(attempt_id=3)
    repo, db = Mock(), Mock()
    repo.session_attempts.return_value = [attempt]
    monkeypatch.setattr(grading_review, '_session', lambda *args: session)
    monkeypatch.setattr(grading_review, 'AssessmentRepository', lambda _: repo)
    monkeypatch.setattr(grading_review, 'question_view', lambda _: NS(question_type=kind))
    with pytest.raises(AppError) as error:
        grading_review.approve(db, 1, 3, GradeReviewRequest(revision=0, score='1'), NS(account_id=4))
    assert error.value.code == 'review_not_allowed'
    db.commit.assert_not_called()


def test_review_detail_only_returns_submitted_essays(monkeypatch):
    session = NS(locale='en')
    attempts = [NS(attempt_id=i, kind=kind, submitted_at=submitted) for i, kind, submitted in
                [(1, 'sql', True), (2, 'mcq', True), (3, 'essay', None)]]
    repo, db = Mock(), Mock()
    repo.session_attempts.return_value = attempts
    db.scalars.return_value = []
    monkeypatch.setattr(grading_review, '_session', lambda *args: session)
    monkeypatch.setattr(grading_review, '_summary', lambda *args: {})
    monkeypatch.setattr(grading_review, 'AssessmentRepository', lambda _: repo)
    monkeypatch.setattr(grading_review, 'question_view', lambda a, locale: NS(question_type=a.kind))
    assert grading_review.detail(db, 1)['items'] == []


@pytest.mark.parametrize("policy,revision,visible", [("IMMEDIATE", 0, False), ("IMMEDIATE", 1, True), ("HUMAN_VERIFIED", 0, True)])
def test_scores_are_visible_but_answers_and_feedback_wait_for_review(monkeypatch, policy, revision, visible):
    now = datetime.now(timezone.utc)
    session = NS(session_id=1, status="completed", locale="en", result_release_policy=policy)
    attempt = NS(attempt_id=2, question_id=3, seq_no=1, review_revision=revision,
                 grading_detail={"feedback": "AI feedback", "rubric_level": "Complete"}, question_snapshot={},
                 selected_option_id=None, selected_option_ids=[], sql_answer=None, essay_answer="My answer",
                 score=Decimal("1"), served_at=now, submitted_at=now)
    question = NS(question_type="essay", prompt="Explain", content_locale="en", explanation="Explanation",
                  reference_answer="Reference answer", difficulty_level=1, points=Decimal("1"), concept_tags=[], options=[], rubrics=[])
    repo = Mock()
    repo.session_attempts.return_value = [attempt]
    monkeypatch.setattr(adaptive_engine, "AssessmentRepository", lambda _: repo)
    monkeypatch.setattr(adaptive_engine, "load_owned_finalized_session", lambda *args: session)
    monkeypatch.setattr(adaptive_engine, "question_view", lambda *args: question)
    item = adaptive_engine.get_evidence(Mock(), 1, NS(account_id=4)).items[0]
    assert item.score == Decimal("1")
    assert item.feedback_pending is not visible
    assert (item.reference_answer is not None) is visible
    assert (item.grading_detail is not None) is visible
