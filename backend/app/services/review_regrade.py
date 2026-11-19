"""PR 3B-5: question reports, deviations, v2 regrade and two-AI analysis.

Machine-graded MCQ/SQL scores are never edited directly. An accepted report
zeroes the question in a new V2 version; essay changes are per criterion with
a reason. Any change above 30% of the question (or criterion) maximum needs a
second administrator, or the documented long-reason path when no other active
administrator exists. V2 becomes official only after the two-AI rewrite.
"""
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import logging

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ..errors import AppError
from ..models import (
    Account,
    AiStageValidation,
    AssessmentSession,
    Attempt,
    QuestionReport,
    ReviewDeviation,
    ReviewRequest,
    SessionResultAnalysis,
    SessionResultCriterionScore,
    SessionResultPublication,
    SessionResultVersion,
    SessionResultVersionScore,
)
from ..repositories import AssessmentRepository
from .ai_stage_service import AiStageService
from .evidence_context import question_view
from .review_flow import (
    LONG_REASON_MIN_CHARS,
    _lock_case,
    _require_not_owner,
    _server_now,
    detail,
)

CENT = Decimal("0.01")
RATIO = Decimal("0.0001")
THRESHOLD = Decimal("0.30")
MACHINE_TYPES = {"mcq", "sql"}
LOG = logging.getLogger("dbcas.review")


def _dec(value):
    return Decimal(str(value if value is not None else 0))


def _attempt(db, case, attempt_id):
    attempt = db.get(Attempt, attempt_id)
    if attempt is None or attempt.session_id != case.session_id:
        raise AppError(404, "attempt_not_found", "Submission not found in this review case")
    return attempt


def _v1(db, case):
    version = db.get(SessionResultVersion, case.base_result_version_id)
    if version is None:
        raise AppError(409, "review_not_eligible", "The base V1 result is missing")
    return version


def _require_claim(db, case, admin):
    if case.claimed_by != admin.account_id:
        raise AppError(409, "review_claim_required",
                       "Only the administrator holding the claim can act on this case")
    now = _server_now(db)
    if case.claim_expires_at is not None and case.claim_expires_at <= now:
        raise AppError(409, "review_claim_expired", "The claim lease expired; reload the queue")


def _require_active(db, case, admin):
    if case.status != "IN_REVIEW":
        raise AppError(409, "review_not_decidable",
                       "The case must be in review", details={"status": case.status})
    _require_claim(db, case, admin)


def _require_editable(case):
    if case.regraded_result_version_id is not None:
        raise AppError(409, "review_already_regraded",
                       "This case already has a V2 result; retry its analysis instead")


def _scores(db, version_id):
    return list(db.scalars(select(SessionResultVersionScore).where(
        SessionResultVersionScore.result_version_id == version_id)))


def _criteria(db, version_id):
    return list(db.scalars(select(SessionResultCriterionScore).where(
        SessionResultCriterionScore.result_version_id == version_id)))


def _other_admins(db, actor_id):
    return int(db.scalar(select(func.pr3a_other_active_admins(actor_id))) or 0)


def _ratio(ai_score, reviewed_score, max_points):
    if max_points <= 0:
        return Decimal(0)
    return (abs(_dec(reviewed_score) - _dec(ai_score)) / _dec(max_points)).quantize(
        RATIO, rounding=ROUND_HALF_UP)


def _deviation(db, case, attempt_id, criterion_id):
    stmt = select(ReviewDeviation).where(
        ReviewDeviation.review_request_id == case.review_request_id,
        ReviewDeviation.attempt_id == attempt_id,
    )
    stmt = (stmt.where(ReviewDeviation.criterion_snapshot_id.is_(None))
            if criterion_id is None
            else stmt.where(ReviewDeviation.criterion_snapshot_id == criterion_id))
    return db.scalar(stmt)


def _deviation_valid(db, row, reviewed_score):
    if row is None or _dec(row.reviewed_score) != _dec(reviewed_score):
        return False
    if row.confirmation == "SECOND_ADMIN":
        return row.second_reviewer_id is not None and row.second_reviewer_id != row.first_reviewer_id
    if row.confirmation == "SINGLE_ADMIN_LONG_REASON":
        return (len((row.reason or "").strip()) >= LONG_REASON_MIN_CHARS
                and _other_admins(db, row.first_reviewer_id) == 0)
    return False


def add_question_report(db, review_request_id, payload, admin):
    case = _lock_case(db, review_request_id)
    if case is None:
        raise AppError(404, "review_not_found", "Review request not found")
    _require_not_owner(db, case, admin)
    _require_active(db, case, admin)
    _require_editable(case)
    attempt = _attempt(db, case, payload.attempt_id)
    kind = question_view(attempt).question_type
    if kind not in MACHINE_TYPES:
        raise AppError(422, "report_not_supported",
                       "Only machine-graded MCQ/SQL questions accept wrong-question reports")
    report = QuestionReport(
        review_request_id=case.review_request_id,
        session_id=case.session_id,
        attempt_id=attempt.attempt_id,
        question_id=attempt.question_id,
        reported_by=admin.account_id,
        category=payload.category,
        details=payload.details.strip(),
    )
    db.add(report)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "question_report_exists",
                       "A report with this category already exists for the question")
    db.commit()
    return detail(db, review_request_id)


def resolve_question_report(db, question_report_id, payload, admin):
    report = db.scalar(select(QuestionReport).where(
        QuestionReport.question_report_id == question_report_id).with_for_update())
    if report is None or report.review_request_id is None:
        raise AppError(404, "question_report_not_found", "Question report not found")
    case = _lock_case(db, report.review_request_id)
    if case is None:
        raise AppError(404, "review_not_found", "Review request not found")
    _require_not_owner(db, case, admin)
    _require_active(db, case, admin)
    _require_editable(case)
    if report.status != "OPEN":
        raise AppError(409, "question_report_closed", "This report is already resolved")
    note = (payload.note or "").strip()
    if len(note) < 10:
        raise AppError(422, "resolution_note_required",
                       "Provide a resolution note of at least 10 characters")
    report.status = payload.status
    report.resolution_note = note
    report.resolved_by = admin.account_id
    report.resolved_at = _server_now(db)
    db.commit()
    return detail(db, case.review_request_id)


def add_deviation(db, review_request_id, payload, admin):
    case = _lock_case(db, review_request_id)
    if case is None:
        raise AppError(404, "review_not_found", "Review request not found")
    _require_not_owner(db, case, admin)
    _require_active(db, case, admin)
    _require_editable(case)
    attempt = _attempt(db, case, payload.attempt_id)
    version = _v1(db, case)
    if payload.criterion_snapshot_id is None:
        base = db.scalar(select(SessionResultVersionScore).where(
            SessionResultVersionScore.result_version_id == version.result_version_id,
            SessionResultVersionScore.attempt_id == attempt.attempt_id))
    else:
        base = db.scalar(select(SessionResultCriterionScore).where(
            SessionResultCriterionScore.result_version_id == version.result_version_id,
            SessionResultCriterionScore.attempt_id == attempt.attempt_id,
            SessionResultCriterionScore.criterion_snapshot_id == payload.criterion_snapshot_id))
    if base is None:
        raise AppError(404, "score_snapshot_not_found", "The base score snapshot was not found")
    max_points = _dec(base.max_points if payload.criterion_snapshot_id is not None
                      else base.max_score)
    ai_score = _dec(base.score)
    ratio = _ratio(ai_score, payload.reviewed_score, max_points)
    if ratio <= THRESHOLD:
        raise AppError(422, "deviation_not_required",
                       "Only changes above 30% require deviation registration")
    reason = (payload.reason or "").strip()
    if reason and len(reason) < 10:
        raise AppError(422, "deviation_reason_required", "Provide a reason of at least 10 characters")
    if payload.second_reviewer_id is not None and payload.second_reviewer_id != admin.account_id:
        second = db.get(Account, payload.second_reviewer_id)
        if second is None or second.status != "active" or not any(
                role.role_name == "Administrator" for role in second.roles):
            raise AppError(422, "invalid_second_reviewer", "The second reviewer must be an active administrator")
        confirmation, second_id = "SECOND_ADMIN", payload.second_reviewer_id
    elif (_other_admins(db, admin.account_id) == 0
          and payload.second_reviewer_id is None
          and len(reason) >= LONG_REASON_MIN_CHARS):
        confirmation, second_id = "SINGLE_ADMIN_LONG_REASON", None
    elif _other_admins(db, admin.account_id) == 0:
        raise AppError(422, "deviation_reason_too_short",
                       f"The single-administrator path requires a reason of at least {LONG_REASON_MIN_CHARS} characters")
    else:
        raise AppError(422, "second_reviewer_required",
                       "Another active administrator must confirm this deviation")
    row = ReviewDeviation(
        review_request_id=case.review_request_id,
        session_id=case.session_id,
        attempt_id=attempt.attempt_id,
        criterion_snapshot_id=payload.criterion_snapshot_id,
        ai_score=ai_score.quantize(CENT, rounding=ROUND_HALF_UP),
        reviewed_score=_dec(payload.reviewed_score).quantize(CENT, rounding=ROUND_HALF_UP),
        max_points=max_points.quantize(CENT, rounding=ROUND_HALF_UP),
        deviation_ratio=ratio,
        reason=reason,
        first_reviewer_id=admin.account_id,
        second_reviewer_id=second_id,
        confirmation=confirmation,
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "deviation_exists", "A deviation for this attempt/criterion already exists")
    db.commit()
    return detail(db, review_request_id)


def confirm_deviation(db, review_request_id, deviation_id, admin):
    case = _lock_case(db, review_request_id)
    if case is None:
        raise AppError(404, "review_not_found", "Review request not found")
    _require_not_owner(db, case, admin)
    row = db.get(ReviewDeviation, deviation_id)
    if row is None or row.review_request_id != case.review_request_id:
        raise AppError(404, "deviation_not_found", "Deviation not found")
    if row.confirmation != "SECOND_ADMIN":
        raise AppError(422, "deviation_not_confirmable", "This deviation does not need a second administrator")
    if row.second_reviewer_id != admin.account_id:
        raise AppError(403, "deviation_confirm_forbidden",
                       "Only the nominated second administrator can confirm this deviation")
    return {"deviation_id": row.deviation_id, "confirmed_by": admin.account_id,
            "confirmed_at": _server_now(db)}


def _question_report_view(row):
    return {
        "question_report_id": row.question_report_id,
        "attempt_id": row.attempt_id,
        "question_id": row.question_id,
        "category": row.category,
        "details": row.details,
        "status": row.status,
        "resolution_note": row.resolution_note,
        "resolved_by": row.resolved_by,
        "resolved_at": row.resolved_at,
    }


def _deviation_view(row):
    return {
        "deviation_id": row.deviation_id,
        "attempt_id": row.attempt_id,
        "criterion_snapshot_id": row.criterion_snapshot_id,
        "ai_score": row.ai_score,
        "reviewed_score": row.reviewed_score,
        "max_points": row.max_points,
        "deviation_ratio": row.deviation_ratio,
        "reason": row.reason,
        "first_reviewer_id": row.first_reviewer_id,
        "second_reviewer_id": row.second_reviewer_id,
        "confirmation": row.confirmation,
        "created_at": row.created_at,
    }


def _analysis_data(db, case, version, session):
    scores = _scores(db, version.result_version_id)
    criteria = _criteria(db, version.result_version_id)
    attempts = {a.attempt_id: a for a in db.scalars(
        select(Attempt).where(Attempt.session_id == session.session_id))}
    by_attempt = {}
    for row in scores:
        attempt = attempts.get(row.attempt_id)
        by_attempt[row.attempt_id] = {
            "attempt_id": row.attempt_id,
            "question_type": question_view(attempt).question_type if attempt else "unknown",
            "score": str(row.score),
            "max_score": str(row.max_score),
            "criteria": [
                {"criterion_snapshot_id": c.criterion_snapshot_id,
                 "score": str(c.score), "max_points": str(c.max_points),
                 "comment": c.comment}
                for c in criteria if c.attempt_id == row.attempt_id
            ],
        }
    reports = list(db.scalars(select(QuestionReport).where(
        QuestionReport.review_request_id == case.review_request_id,
        QuestionReport.status == "ACCEPTED")))
    deviations = list(db.scalars(select(ReviewDeviation).where(
        ReviewDeviation.review_request_id == case.review_request_id)))
    return {
        "session_id": session.session_id,
        "result_version": {
            "version_no": version.version_no,
            "total_score": str(version.total_score),
            "max_score": str(version.max_score),
        },
        "attempts": [by_attempt[key] for key in sorted(by_attempt)],
        "accepted_question_reports": [
            {"attempt_id": r.attempt_id, "category": r.category,
             "details": r.details, "resolution_note": r.resolution_note}
            for r in reports
        ],
        "deviations": [
            {"deviation_id": d.deviation_id, "attempt_id": d.attempt_id,
             "criterion_snapshot_id": d.criterion_snapshot_id,
             "ai_score": str(d.ai_score), "reviewed_score": str(d.reviewed_score),
             "max_points": str(d.max_points), "deviation_ratio": str(d.deviation_ratio),
             "reason": d.reason, "first_reviewer_id": d.first_reviewer_id,
             "second_reviewer_id": d.second_reviewer_id,
             "confirmation": d.confirmation}
            for d in deviations
        ],
    }


def _run_analysis(db, case, version, session, admin, llm):
    from ..config import get_settings
    service = AiStageService(
        db, llm=llm, settings=get_settings(),
        scope_key=f"v2:{case.review_request_id}", run_mode="V2_ANALYSIS",
        validator_version="pr3b5-regrade-v2",
    )
    data = _analysis_data(db, case, version, session)
    ai1 = service.run_ai1(session_id=session.session_id, data=data,
                          admin_reason=case.resolution_note,
                          result_version_id=version.result_version_id)
    validation = db.scalar(select(AiStageValidation).where(
        AiStageValidation.stage_run_id == ai1.stage_run_id,
        AiStageValidation.status == "VALID"))
    if validation is None:
        raise AppError(409, "analysis_predecessor_missing", "AI1 validation is missing")
    ai2 = service.run_ai2(session_id=session.session_id,
                          predecessor_validation_id=validation.validation_id,
                          result_version_id=version.result_version_id)
    publication = db.get(SessionResultPublication, version.result_version_id)
    analysis = SessionResultAnalysis(
        session_id=session.session_id,
        result_version_id=version.result_version_id,
        ai1_run_id=ai1.stage_run_id,
        ai2_run_id=ai2.stage_run_id,
        analysis_schema_version=1,
        analysis_hash=ai2.output_hash or "",
        analysis=ai2.output or {},
    )
    db.add(analysis)
    publication.state = "OFFICIAL"
    session.current_result_version_id = version.result_version_id
    case.status = "REGRADED"
    case.resolved_by = admin.account_id
    case.resolved_at = _server_now(db)
    db.commit()
    return "OFFICIAL"


def _finish_analysis(db, case, version, session, admin, llm):
    try:
        return _run_analysis(db, case, version, session, admin, llm)
    except Exception as exc:
        # Stable, secret-free category only; never log prompt or answer text.
        LOG.warning("v2 analysis failed request=%s code=%s",
                    case.review_request_id,
                    getattr(exc, "code", None) or type(exc).__name__)
        db.rollback()
        publication = db.get(SessionResultPublication, version.result_version_id)
        if publication is not None:
            publication.state = "ANALYSIS_FAILED"
            db.commit()
        return "ANALYSIS_FAILED"


def approve(db, review_request_id, payload, admin, llm):
    case = _lock_case(db, review_request_id)
    if case is None:
        raise AppError(404, "review_not_found", "Review request not found")
    _require_not_owner(db, case, admin)
    if case.revision != payload.expected_revision:
        raise AppError(409, "review_conflict", "The review case changed. Reload it.")
    _require_active(db, case, admin)
    _require_editable(case)
    session = db.get(AssessmentSession, case.session_id)
    version = _v1(db, case)
    note = (payload.note or "").strip()
    if len(note) < 10:
        raise AppError(422, "review_reason_required", "Provide a decision reason of at least 10 characters")

    scores = _scores(db, version.result_version_id)
    criteria = _criteria(db, version.result_version_id)
    attempts = {a.attempt_id: a for a in db.scalars(
        select(Attempt).where(Attempt.session_id == case.session_id))}
    reports = list(db.scalars(select(QuestionReport).where(
        QuestionReport.review_request_id == review_request_id)))
    if any(row.status == "OPEN" for row in reports):
        raise AppError(422, "question_reports_pending", "Resolve every question report before approving")
    accepted = {row.attempt_id for row in reports if row.status == "ACCEPTED"}

    changes = {}
    for item in payload.criterion_scores:
        attempt = attempts.get(item.attempt_id)
        if attempt is None:
            raise AppError(404, "attempt_not_found", "Submission not found in this review case")
        if question_view(attempt).question_type != "essay":
            raise AppError(422, "criterion_change_not_allowed",
                           "Per-criterion changes apply to essay answers only")
        base = next((c for c in criteria
                     if c.attempt_id == item.attempt_id
                     and c.criterion_snapshot_id == item.criterion_snapshot_id), None)
        if base is None:
            raise AppError(404, "score_snapshot_not_found", "The criterion snapshot was not found")
        if not Decimal(0) <= item.score <= _dec(base.max_points):
            raise AppError(422, "invalid_review_score", "A score within the criterion maximum is required")
        ratio = _ratio(base.score, item.score, base.max_points)
        if ratio > THRESHOLD and not _deviation_valid(
                db, _deviation(db, case, item.attempt_id, item.criterion_snapshot_id), item.score):
            raise AppError(422, "deviation_confirmation_required",
                           "A confirmed >30% deviation is required for this criterion change")
        changes[(item.attempt_id, item.criterion_snapshot_id)] = item

    for row in scores:
        if row.attempt_id not in accepted:
            continue
        attempt = attempts.get(row.attempt_id)
        if attempt is None or question_view(attempt).question_type not in MACHINE_TYPES:
            raise AppError(422, "report_not_supported",
                           "Only machine-graded MCQ/SQL questions can be zeroed by a report")
        if _ratio(row.score, 0, row.max_score) > THRESHOLD and not _deviation_valid(
                db, _deviation(db, case, row.attempt_id, None), 0):
            raise AppError(422, "deviation_confirmation_required",
                           "A confirmed >30% deviation is required to zero this question")

    prepared = []
    for row in scores:
        attempt = attempts.get(row.attempt_id)
        kind = question_view(attempt).question_type if attempt else "unknown"
        if row.attempt_id in accepted:
            prepared.append((row, Decimal(0), []))
            continue
        if kind != "essay":
            prepared.append((row, _dec(row.score), []))
            continue
        v1_criteria = [c for c in criteria if c.attempt_id == row.attempt_id]
        new_criteria = []
        for base in v1_criteria:
            change = changes.get((row.attempt_id, base.criterion_snapshot_id))
            new_criteria.append((base, _dec(change.score) if change else _dec(base.score),
                                 change.reason if change else base.comment))
        prepared.append((row, sum((value for _, value, _ in new_criteria), Decimal(0)), new_criteria))

    total = sum((score for _, score, _ in prepared), Decimal(0))
    maximum = sum((_dec(row.max_score) for row, _, _ in prepared), Decimal(0))
    parts = [(row.attempt_id, str(score), str(maximum_row.max_score))
             for row, score, _ in prepared for maximum_row in [row]]
    result_hash = hashlib.sha256(json.dumps(
        ["v2", case.review_request_id, parts], sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    next_no = (db.scalar(select(func.max(SessionResultVersion.version_no)).where(
        SessionResultVersion.session_id == case.session_id)) or 0) + 1
    v2 = SessionResultVersion(
        session_id=case.session_id,
        version_no=next_no,
        source="V2",
        supersedes_version_id=version.result_version_id,
        total_score=total,
        max_score=maximum,
        result_hash=result_hash,
        approved_by=admin.account_id,
        approved_review_revision=case.revision,
        review_request_id=case.review_request_id,
    )
    db.add(v2)
    db.flush()
    for row, score, new_criteria in prepared:
        db.add(SessionResultVersionScore(
            session_id=case.session_id,
            result_version_id=v2.result_version_id,
            attempt_id=row.attempt_id,
            score=score,
            max_score=row.max_score,
            source="REVIEW",
        ))
        db.flush()
        for base, value, comment in new_criteria:
            db.add(SessionResultCriterionScore(
                session_id=case.session_id,
                result_version_id=v2.result_version_id,
                attempt_id=row.attempt_id,
                criterion_snapshot_id=base.criterion_snapshot_id,
                score=value,
                max_points=base.max_points,
                comment=comment,
            ))
        db.flush()
    db.add(SessionResultPublication(
        result_version_id=v2.result_version_id,
        session_id=case.session_id,
        state="APPROVED_PENDING_ANALYSIS",
    ))
    case.regraded_result_version_id = v2.result_version_id
    case.resolution_note = note
    db.commit()
    _finish_analysis(db, case, v2, session, admin, llm)
    return detail(db, review_request_id)


def retry_analysis(db, review_request_id, admin, llm):
    case = _lock_case(db, review_request_id)
    if case is None:
        raise AppError(404, "review_not_found", "Review request not found")
    _require_not_owner(db, case, admin)
    _require_active(db, case, admin)
    if case.regraded_result_version_id is None:
        raise AppError(409, "analysis_not_ready", "No V2 result exists for this case")
    version = db.get(SessionResultVersion, case.regraded_result_version_id)
    publication = db.get(SessionResultPublication, version.result_version_id)
    if publication is None or publication.state != "ANALYSIS_FAILED":
        raise AppError(409, "analysis_not_failed", "Only a failed analysis can be retried")
    publication.state = "APPROVED_PENDING_ANALYSIS"
    db.commit()
    session = db.get(AssessmentSession, case.session_id)
    _finish_analysis(db, case, version, session, admin, llm)
    return detail(db, review_request_id)
