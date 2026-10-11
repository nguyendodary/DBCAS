"""Bounded, database-leased grading retry jobs; no external queue required."""
from datetime import datetime, timedelta, timezone

from ..config import get_settings
from ..models import Account, Attempt
from ..repositories import AssessmentRepository
from .assessment_lifecycle import grade_attempt, persist_grade
from .llm import LLMError
from .sandbox_runner import SandboxError
from ..errors import AppError


def process_one(db, runner, llm=None, *, include_essay=False, settings=None):
    settings = settings or get_settings()
    repo = AssessmentRepository(db)
    job = repo.claim_grading_job(include_essay=include_essay)
    if job is None:
        return False
    job_id = job.job_id
    attempt_id = job.attempt_id
    claim_count = job.attempt_count
    db.commit()  # durable lease; provider work never holds the claim lock
    attempt = db.get(Attempt, attempt_id)
    db.refresh(attempt)
    session = repo.get_session(attempt.session_id)
    learner = db.get(Account, session.learner_id)
    answer = {key: getattr(attempt, key) for key in ("selected_option_id", "sql_answer", "essay_answer")}
    error = None
    try:
        result = grade_attempt(repo, attempt, learner, answer, runner, llm)
    except (LLMError, SandboxError, AppError) as exc:
        error = exc
    repo.lock_session(session.session_id)
    job = repo.lock_grading_job(job_id)
    if job.status != "processing" or job.attempt_count != claim_count:
        db.rollback()  # another worker recovered this lease; do not publish
        return True
    if error:
        job.last_error_code = error.code
        job.lease_until = None
        if job.attempt_count >= settings.grading_job_max_attempts or isinstance(error, AppError):
            job.status = "failed"
            job.finished_at = datetime.now(timezone.utc)
            attempt.grading_status = "failed"
        else:
            job.status = "pending"
            job.available_at = datetime.now(timezone.utc) + timedelta(seconds=settings.grading_job_retry_seconds * job.attempt_count)
        attempt.grading_detail = {**(attempt.grading_detail or {}), "status": attempt.grading_status, "error_code": error.code}
        db.commit()
    else:
        persist_grade(attempt, result)
        job.status = "completed"
        job.finished_at = datetime.now(timezone.utc)
        job.lease_until = None
        job.last_error_code = None
        db.flush()
        if session.status != "in_progress":
            from .competency_service import detect_session_gaps
            detect_session_gaps(db, session)
        else:
            db.commit()
    return True
