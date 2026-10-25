"""Transactional draft/submission/finalization rules owned by the server."""
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal

from ..errors import AppError
from ..repositories import AssessmentRepository
from ..schemas import AttemptResult, DraftResult, SubmitAnswerRequest
from .evidence_context import capture_assessment, capture_question, question_view
from .llm import LLMError
from .llm.sanitize import profile_identifiers
from .sandbox_runner import SandboxError


def owned_locked_session(db, session_id, learner):
    repo = AssessmentRepository(db)
    session = repo.lock_session(session_id)
    if session is None or session.learner_id != learner.account_id:
        raise AppError(404, "session_not_found", "Assessment session not found")
    if session.config_snapshot is None:
        session.config_snapshot = capture_assessment(repo.get_assessment(session.assessment_id))
    return session


def _answer_dict(payload, question):
    fields = {"mcq": "selected_option_id", "sql": "sql_answer", "essay": "essay_answer"}
    field = fields[question.question_type]
    multiple = getattr(payload, "selected_option_ids", None)
    if question.question_type == "mcq":
        if payload.sql_answer is not None or payload.essay_answer is not None:
            raise AppError(422, "answer_type_mismatch", "The answer format does not match the served question")
        if multiple is not None:
            if payload.selected_option_id is not None:
                raise AppError(422, "answer_type_mismatch", "Send either one option or a list of options")
            values = multiple
        else:
            values = [payload.selected_option_id] if payload.selected_option_id is not None else []
        if len(values) != len(set(values)) or not set(values).issubset({o.option_id for o in question.options}):
            raise AppError(422, "invalid_option", "Selected options must be unique and belong to this question")
        return {"selected_option_ids": sorted(values)} if multiple is not None else {field: payload.selected_option_id}
    if multiple is not None or any(getattr(payload, other) is not None for other in fields.values() if other != field):
        raise AppError(422, "answer_type_mismatch", "The answer format does not match the served question")
    return {field: getattr(payload, field)}


def _hash(answer):
    return hashlib.sha256(json.dumps(answer, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _snapshot(repo, attempt):
    if attempt.question_snapshot is None:
        attempt.question_snapshot = capture_question(repo, attempt.question)
    return question_view(attempt)


def _expired(session, now):
    expiry = session.expires_at.replace(tzinfo=timezone.utc) if session.expires_at.tzinfo is None else session.expires_at
    return now >= expiry


def _require_active(db, session):
    if session.status != "in_progress":
        raise AppError(409, "session_not_active", "Session is no longer in progress")
    if _expired(session, AssessmentRepository(db).server_time()):
        finalize(db, session, timed_out=True)
        raise AppError(409, "session_expired", "Session time has expired")


def _attempt(repo, session_id, question_id):
    attempt = repo.get_attempt(session_id, question_id)
    if attempt is None:
        raise AppError(404, "question_not_served", "This question was not served in the session")
    return attempt


def save_draft(db, session_id, learner, payload):
    session = owned_locked_session(db, session_id, learner)
    _require_active(db, session)
    repo = AssessmentRepository(db)
    attempt = _attempt(repo, session_id, payload.question_id)
    if attempt.submitted_at is not None:
        raise AppError(409, "already_submitted", "This question was already answered")
    answer = _answer_dict(payload, _snapshot(repo, attempt))
    if payload.revision == attempt.draft_revision and answer == attempt.draft_answer:
        return draft_result(attempt)
    if payload.revision != attempt.draft_revision + 1:
        raise AppError(409, "draft_revision_conflict", "A newer saved draft exists. Reload it before saving.", details={"revision": attempt.draft_revision})
    attempt.draft_answer = answer
    attempt.draft_revision = payload.revision
    attempt.draft_saved_at = repo.server_time()
    db.commit()
    return draft_result(attempt)


def draft_result(attempt):
    return DraftResult(question_id=attempt.question_id, answer=attempt.draft_answer, revision=attempt.draft_revision, saved_at=attempt.draft_saved_at)


def get_draft(db, session_id, learner, question_id):
    session = owned_locked_session(db, session_id, learner)
    if session.status == "in_progress" and _expired(session, AssessmentRepository(db).server_time()):
        finalize(db, session, timed_out=True)
    return draft_result(_attempt(AssessmentRepository(db), session_id, question_id))


def grade_attempt(repo, attempt, learner, answer, runner, llm):
    from .grading_service import score_mcq
    from .sql_grading import grade_sql
    from .essay_grading import grade_essay
    question = _snapshot(repo, attempt)
    if question.question_type == "mcq":
        return score_mcq(question, question.options, answer.get("selected_option_id"), answer.get("selected_option_ids"))
    if question.question_type == "sql":
        if runner is None:
            raise SandboxError("sandbox_unavailable", "SQL grading is temporarily unavailable")
        datasets = question.datasets
        if not datasets:
            raise AppError(422, "dataset_not_configured", "This SQL question has no test datasets configured")
        required = [getattr(t.concept, "sql_feature", None) or t.concept.concept_name for t in question.concept_tags if t.confirmed and t.is_required]
        return grade_sql(question, datasets, required, answer["sql_answer"], runner)
    if llm is None:
        raise LLMError(LLMError.UNAVAILABLE, "Essay grading is temporarily unavailable")
    if not question.rubrics:
        raise AppError(422, "rubric_not_configured", "This essay question has no rubric configured")
    return grade_essay(
        question, question.rubrics, answer["essay_answer"], llm,
        identifiers=profile_identifiers(learner),
        locale=getattr(attempt.session, "locale", "en") or "en",
    )


def persist_grade(attempt, result):
    attempt.score = result["score"]
    attempt.grading_detail = result["grading_detail"]
    attempt.grading_status = "graded"


def _persist_answer(attempt, answer, submitted_at):
    for field, value in answer.items():
        setattr(attempt, field, value)
    if "selected_option_ids" in answer:
        values = answer["selected_option_ids"]
        attempt.selected_option_id = values[0] if len(values) == 1 else None
    elif "selected_option_id" in answer:
        attempt.selected_option_ids = [answer["selected_option_id"]] if answer["selected_option_id"] is not None else []
    attempt.submitted_at = submitted_at
    attempt.submission_hash = _hash(answer)


def result_for(attempt):
    question = question_view(attempt)
    is_correct = (attempt.grading_detail or {}).get("rubric_level") == "Complete" if question.question_type == "essay" and (attempt.grading_detail or {}).get("grader") != "human_verified" else attempt.score is not None and attempt.score >= question.points
    hidden = attempt.session.result_release_policy == "HUMAN_VERIFIED" and attempt.session.release_status != "published"
    return AttemptResult(attempt_id=attempt.attempt_id, session_id=attempt.session_id, question_id=attempt.question_id,
                         score=None if hidden else attempt.score, points_possible=question.points, is_correct=None if hidden else is_correct,
                         submitted_at=attempt.submitted_at, grading_status=attempt.grading_status)


def submit(db, session_id, learner, payload, runner=None, llm=None, *, idempotent=True):
    session = owned_locked_session(db, session_id, learner)
    if (session.config_snapshot or {}).get("navigation_mode") == "FREE":
        raise AppError(409, "finish_required", "Save your answer as a draft and submit the whole assessment to receive a grade")
    repo = AssessmentRepository(db)
    attempt = _attempt(repo, session_id, payload.question_id)
    question = _snapshot(repo, attempt)
    answer = _answer_dict(payload, question)
    if attempt.submitted_at is not None:
        if idempotent and attempt.submission_hash == _hash(answer):
            return result_for(attempt)
        raise AppError(409, "already_submitted", "This question was already answered")
    _require_active(db, session)
    if question.question_type != "mcq" and not (next(iter(answer.values())) or "").strip():
        raise AppError(422, "empty_answer", "An answer is required for this question")
    submitted_at = repo.server_time()
    try:
        result = grade_attempt(repo, attempt, learner, answer, runner, llm)
    except (LLMError, SandboxError) as exc:
        if isinstance(exc, LLMError) and exc.code == LLMError.INVALID_RESPONSE and session.result_release_policy != "HUMAN_VERIFIED":
            # Invalid scoring must not fabricate evidence or enter the cache.
            raise exc.to_app_error()
        _persist_answer(attempt, answer, submitted_at)
        attempt.grading_detail = {"grader": "pending", "question_type": question.question_type, "status": "pending", "error_code": exc.code, "points_possible": str(question.points)}
        repo.enqueue_grading(attempt)
    else:
        _persist_answer(attempt, answer, submitted_at)
        persist_grade(attempt, result)
    db.flush()
    return result_for(attempt)  # caller commits answer + next state together


def finalize(db, session, *, timed_out=False):
    """Finalize once; persist and grade/queue saved drafts in the same commit."""
    repo = AssessmentRepository(db)
    session = repo.lock_session(session.session_id)
    if session.status != "in_progress":
        return session
    now = repo.server_time()
    timed_out = timed_out or _expired(session, now)
    timestamp = session.expires_at if timed_out else now
    for attempt in repo.session_attempts(session.session_id):
        if attempt.submitted_at is not None or not attempt.draft_answer:
            continue
        question = _snapshot(repo, attempt)
        answer = attempt.draft_answer
        value = next(iter(answer.values()), None)
        if value is None or value == [] or isinstance(value, str) and not value.strip():
            continue
        _persist_answer(attempt, answer, timestamp)
        if question.question_type == "mcq":
            persist_grade(attempt, grade_attempt(repo, attempt, None, answer, None, None))
        else:
            attempt.grading_detail = {"grader": "pending", "question_type": question.question_type, "status": "pending", "points_possible": str(question.points)}
            repo.enqueue_grading(attempt)
    session.status = "timed_out" if timed_out else "completed"
    session.submitted_at = timestamp
    db.flush()
    from .competency_service import detect_session_gaps
    detect_session_gaps(db, session, commit=False)
    from .grading_review import reconcile
    reconcile(db, session)
    # Empty evidence/pending grades still need a durable finalization. Keep
    # session, drafts, jobs, competency and gaps inside the same transaction.
    db.commit()
    return session


def sweep_expired(db):
    repo = AssessmentRepository(db)
    count = 0
    for session_id in repo.expired_session_ids():
        session = repo.lock_session(session_id)
        if session and session.status == "in_progress" and _expired(session, repo.server_time()):
            finalize(db, session, timed_out=True)
            count += 1
    return count
