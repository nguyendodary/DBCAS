"""SQL capacity is admission control; an ungradable row cannot starve others."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.models import AssessmentSession, Attempt, GradingJob
from app.repositories import AssessmentRepository
from app.services import evaluation_service, grading_jobs
from app.services.evidence_context import capture_question
from test_adaptive_engine import _make_account
from test_ai_admin import _mcq_question
from test_draft_lifecycle import _fixture


def test_sql_capacity_wait_does_not_claim_or_exhaust_a_grading_attempt(db_session, sandbox_runner):
    _, _, attempt, _, _, _, answer = _fixture(db_session, "sql")
    attempt.sql_answer = answer["sql_answer"]
    attempt.submitted_at = datetime.now(timezone.utc)
    repo = AssessmentRepository(db_session)
    repo.enqueue_grading(attempt)
    db_session.commit()
    class CapacityRunner:
        admitted = False

        @contextmanager
        def grading_capacity(self):
            yield self.admitted

        def __getattr__(self, name):
            assert self.admitted, "SQL started without an admitted slot"
            return getattr(sandbox_runner, name)
    runner = CapacityRunner()
    assert grading_jobs.process_one(db_session, runner) is False
    job = db_session.scalar(select(GradingJob))
    assert job.status == "pending" and job.attempt_count == 0 and job.lease_until is None
    assert attempt.score is None and attempt.sql_answer == answer["sql_answer"]
    runner.admitted = True
    assert grading_jobs.process_one(db_session, runner) is True
    db_session.refresh(job); db_session.refresh(attempt)
    assert job.status == "completed" and job.attempt_count == 1
    assert attempt.grading_status == "graded" and attempt.score == Decimal(1)


def test_failed_frozen_sql_cannot_block_another_learners_ready_evaluation(db_session):
    learner, blocked, attempt, question, _, _, _ = _fixture(db_session, "sql")
    blocked.status, blocked.release_status = "completed", "grading_failed"
    attempt.submitted_at, attempt.grading_status = datetime.now(timezone.utc), "failed"
    attempt.question_snapshot = capture_question(AssessmentRepository(db_session), question)
    # Even a subsequently changed live type must not override frozen SQL.
    question.question_type = "essay"
    other = _make_account(db_session, "ready-evaluation@test.dev", "Learner")
    mcq = _mcq_question(db_session, learner, status="validated")
    ready = AssessmentSession(assessment_id=blocked.assessment_id, learner_id=other.account_id,
        status="completed", release_status="published", expires_at=datetime.now(timezone.utc))
    db_session.add(ready); db_session.flush()
    db_session.add(Attempt(session_id=ready.session_id, question_id=mcq.question_id, seq_no=1,
        score=Decimal(1), grading_status="graded", submitted_at=datetime.now(timezone.utc)))
    db_session.commit()
    db_session.expire_all()  # Match the normalized Numeric values of a fresh API transaction.
    first, _, _ = evaluation_service.ensure(db_session, learner.account_id, blocked.session_id)
    first.updated_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    second, _, _ = evaluation_service.ensure(db_session, other.account_id, ready.session_id)
    db_session.commit()
    assert evaluation_service.process_one(db_session) is True
    db_session.refresh(first); db_session.refresh(second); db_session.refresh(attempt)
    assert first.status == "pending" and attempt.score is None
    assert second.status == "ready" and second.payload["evaluation"]["question_comments"]
