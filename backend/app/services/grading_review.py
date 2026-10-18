"""Publication boundary and auditable administrator verification of grades."""
from decimal import Decimal

from sqlalchemy import select

from ..errors import AppError
from ..repositories import AssessmentRepository
from .evidence_context import question_view


def is_published(session):
    return session.status != "in_progress" and session.release_status == "published"


def require_published(session):
    if not is_published(session):
        raise AppError(409, "results_pending", "Official results are not available yet.",
                       details={"release_status": session.release_status,
                                "result_release_policy": session.result_release_policy})


def transition(db, session, status, *, reviewer_id=None):
    from ..models import ResultReleaseEvent
    if session.release_status != status:
        db.add(ResultReleaseEvent(session_id=session.session_id,
            previous_status=session.release_status, new_status=status, reviewer_id=reviewer_id))
        session.release_status = status
        session.review_revision += 1
        if status == "published":
            session.published_at = AssessmentRepository(db).server_time()


def reconcile(db, session, *, reviewer_id=None):
    """Caller holds the session row lock; never publish human-mode implicitly."""
    from ..models import GradeReview
    if is_published(session):
        return
    if session.status == "in_progress":
        return
    attempts = [a for a in AssessmentRepository(db).session_attempts(session.session_id)
                if a.submitted_at is not None]
    if any(a.grading_status == "failed" for a in attempts):
        status = "grading_failed"
    elif any(a.score is None or a.grading_status != "graded" for a in attempts):
        status = "auto_grading"
    elif session.result_release_policy == "IMMEDIATE":
        status = "published"
    else:
        required = {a.attempt_id for a in attempts if question_view(a).question_type in {"sql", "essay"}}
        reviewed = set(db.scalars(select(GradeReview.attempt_id).where(GradeReview.attempt_id.in_(required)))) if required else set()
        status = "reviewed" if required <= reviewed else "pending_review"
    transition(db, session, status, reviewer_id=reviewer_id)


def _session(db, session_id):
    session = AssessmentRepository(db).lock_session(session_id)
    if session is None:
        raise AppError(404, "session_not_found", "Assessment session not found")
    return session


def list_pending(db, *, limit=100, offset=0):
    from ..models import AssessmentSession
    sessions = list(db.scalars(select(AssessmentSession).where(
        AssessmentSession.status != "in_progress",
        ((AssessmentSession.result_release_policy == "HUMAN_VERIFIED") & (AssessmentSession.release_status != "published")) |
        (AssessmentSession.release_status == "grading_failed"))
        .order_by(AssessmentSession.submitted_at, AssessmentSession.session_id).limit(limit).offset(offset)))
    return [_summary(db, session) for session in sessions]


def _summary(db, session):
    from ..models import Account
    learner = db.get(Account, session.learner_id)
    return {"session_id": session.session_id, "learner_id": session.learner_id,
            "learner_name": learner.profile.full_name if learner.profile else learner.email,
            "assessment_title": (session.config_snapshot or {}).get("title", session.assessment.title),
            "release_status": session.release_status, "result_release_policy": session.result_release_policy,
            "submitted_at": session.submitted_at, "revision": session.review_revision}


def detail(db, session_id):
    from ..models import GradeReview, ResultReleaseEvent
    session = _session(db, session_id)
    items = []
    for attempt in AssessmentRepository(db).session_attempts(session_id):
        question = question_view(attempt, session.locale or "en")
        review = db.scalar(select(GradeReview).where(GradeReview.attempt_id == attempt.attempt_id))
        items.append({"attempt_id": attempt.attempt_id, "question_id": attempt.question_id,
            "question_type": question.question_type, "prompt": question.prompt,
            "reference_answer": question.reference_answer, "points": question.points,
            "selected_option_id": attempt.selected_option_id,
            "options": [dict(option_id=o.option_id, option_text=o.option_text, is_correct=o.is_correct) for o in question.options],
            "sql_answer": attempt.sql_answer, "essay_answer": attempt.essay_answer,
            "submitted_at": attempt.submitted_at, "grading_status": attempt.grading_status,
            "automated_score": review.automated_score if review else attempt.score,
            "automated_detail": review.automated_detail if review else attempt.grading_detail,
            "final_score": attempt.score if review else None, "revision": attempt.review_revision,
            "review": {"reviewer_id": review.reviewer_id, "reviewed_at": review.reviewed_at,
                       "comments": review.comments, "approved_score": review.approved_score} if review else None,
            "rubrics": [dict(level_name=r.level_name, min_score=r.min_score, max_score=r.max_score, criteria=r.criteria) for r in question.rubrics]})
    events = list(db.scalars(select(ResultReleaseEvent).where(ResultReleaseEvent.session_id == session_id)
                            .order_by(ResultReleaseEvent.event_id)))
    return {**_summary(db, session), "items": items,
            "events": [{"previous_status": e.previous_status, "new_status": e.new_status,
                        "reviewer_id": e.reviewer_id, "created_at": e.created_at} for e in events]}


def approve(db, session_id, attempt_id, payload, admin):
    from ..models import GradeReview
    session = _session(db, session_id)
    if session.learner_id == admin.account_id:
        raise AppError(403, "self_review_forbidden", "A grader cannot review their own assessment")
    if session.status == "in_progress" or session.result_release_policy != "HUMAN_VERIFIED" or is_published(session):
        raise AppError(409, "review_not_allowed", "Only unpublished, submitted human-verification assessments can be reviewed")
    attempt = next((a for a in AssessmentRepository(db).session_attempts(session_id) if a.attempt_id == attempt_id), None)
    if attempt is None:
        raise AppError(404, "attempt_not_found", "Submission not found")
    if attempt.review_revision != payload.revision or attempt.review_revision > 0:
        raise AppError(409, "review_conflict", "This submission was already reviewed. Reload the latest review.")
    if attempt.submitted_at is None or attempt.grading_status not in {"graded", "failed", "pending"}:
        raise AppError(409, "grading_not_complete", "Wait for automatic grading or a terminal grading failure before reviewing")
    score = payload.score if payload.score is not None else attempt.score
    if score is None or not Decimal(0) <= score <= question_view(attempt).points:
        raise AppError(422, "invalid_review_score", "A final score within the question's points range is required")
    comments = (payload.comments or "").strip() or None
    if attempt.grading_status in {"failed", "pending"} and (not comments or payload.score is None):
        raise AppError(422, "review_comment_required", "Supply an explicit score and explanation to take over incomplete automatic grading")
    from ..models import GradingJob
    job_id = db.scalar(select(GradingJob.job_id).where(GradingJob.attempt_id == attempt_id))
    if job_id:
        job = AssessmentRepository(db).lock_grading_job(job_id)
        job.status = "completed"
        job.finished_at = AssessmentRepository(db).server_time()
        job.lease_until = None
        job.last_error_code = "human_review_completed"
    db.add(GradeReview(attempt_id=attempt_id, reviewer_id=admin.account_id,
        automated_score=attempt.score, automated_detail=attempt.grading_detail,
        approved_score=score, comments=comments))
    attempt.score = score
    attempt.grading_status = "graded"
    attempt.review_revision += 1
    attempt.grading_detail = {"grader": "human_verified", "points_earned": str(score),
        "points_possible": str(question_view(attempt).points), "reviewer_comments": comments,
        "automated_evaluation": attempt.grading_detail}
    session.review_revision += 1
    db.flush()
    from .competency_service import detect_session_gaps
    detect_session_gaps(db, session, commit=False)
    reconcile(db, session, reviewer_id=admin.account_id)
    db.commit()
    return detail(db, session_id)


def publish(db, session_id, payload, admin):
    session = _session(db, session_id)
    if session.learner_id == admin.account_id:
        raise AppError(403, "self_review_forbidden", "A grader cannot publish their own assessment")
    if session.review_revision != payload.revision:
        raise AppError(409, "review_conflict", "The review changed. Reload it before publishing.")
    if is_published(session):
        return detail(db, session_id)
    reconcile(db, session, reviewer_id=admin.account_id)
    if session.result_release_policy != "HUMAN_VERIFIED" or session.release_status != "reviewed":
        raise AppError(409, "review_incomplete", "Complete automatic grading and all required SQL/essay reviews before publishing")
    from .competency_service import detect_session_gaps
    detect_session_gaps(db, session, commit=False)
    transition(db, session, "published", reviewer_id=admin.account_id)
    session.published_at = AssessmentRepository(db).server_time()
    db.commit()
    return detail(db, session_id)


def retry_failed(db, session_id, payload, admin):
    """Requeue terminal failures without making a provider call in this API."""
    from ..models import GradingJob
    session = _session(db, session_id)
    if session.review_revision != payload.revision:
        raise AppError(409, "review_conflict", "The grading state changed. Reload it before retrying.")
    if session.status == "in_progress" or is_published(session) or session.release_status != "grading_failed":
        raise AppError(409, "grading_retry_not_allowed", "Only submitted, failed grading can be retried")
    repo = AssessmentRepository(db)
    for attempt in repo.session_attempts(session_id):
        if attempt.grading_status != "failed" or attempt.review_revision:
            continue
        job_id = db.scalar(select(GradingJob.job_id).where(GradingJob.attempt_id == attempt.attempt_id))
        if job_id:
            job = repo.lock_grading_job(job_id)
            job.status = "pending"
            job.attempt_count = 0
            job.available_at = repo.server_time()
            job.finished_at = None
            job.lease_until = None
        else:
            repo.enqueue_grading(attempt)
        attempt.grading_status = "pending"
        attempt.grading_detail = {**(attempt.grading_detail or {}), "status": "pending"}
    db.flush()
    reconcile(db, session, reviewer_id=admin.account_id)
    db.commit()
    return detail(db, session_id)
