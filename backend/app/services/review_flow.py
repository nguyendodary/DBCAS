"""PR 3B-3: learner review requests and the administrator review queue.

A review case is the only route to a v2 result. This module records intent,
leases a case to one administrator and supports the REJECT branch only; v2
regrading (and the APPROVE branch) belongs to PR 3B-5.
"""
from datetime import timedelta
from uuid import UUID

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError

from ..errors import AppError
from ..models import (
    Account,
    AiStageAttempt,
    AiStageRun,
    AssessmentSession,
    ReviewRequest,
    SessionResultPublication,
    SessionResultVersion,
)
from ..repositories import AssessmentRepository
from ..schemas import ReviewRequestView, UserReviewRequestView
from .ai_stage_service import ACTIVE_STATUSES
from .result_version import is_ai_official

REVIEW_WINDOW_DAYS = 7
CLAIM_LEASE_MINUTES = 30
CASE_TTL_DAYS = 30
LONG_REASON_MIN_CHARS = 120
REVIEW_STATUSES = ("REQUESTED", "IN_REVIEW", "REGRADED", "REJECTED", "EXPIRED")


def _server_now(db):
    return AssessmentRepository(db).server_time()


def _is_admin(account) -> bool:
    return any(role.role_name == "Administrator" for role in account.roles)


def _official_v1(db, session):
    """The published V1 row a learner case must be based on, or ``None``."""
    if not is_ai_official(session) or session.current_result_version_id is None:
        return None
    version = db.get(SessionResultVersion, session.current_result_version_id)
    if version is None or version.source != "V1" or version.version_no != 1:
        return None
    publication = db.scalar(
        select(SessionResultPublication).where(
            SessionResultPublication.result_version_id == version.result_version_id
        )
    )
    if publication is None or publication.state != "OFFICIAL" or publication.published_at is None:
        return None
    return version, publication


def review_window_end(publication):
    return publication.published_at + timedelta(days=REVIEW_WINDOW_DAYS)


def _case_for_session(db, session_id):
    return db.scalar(select(ReviewRequest).where(ReviewRequest.session_id == session_id))


def review_meta(db, session):
    """Review fields merged into the existing session/result responses.

    ``review_status`` keeps the published result state (``OFFICIAL``) until a
    case exists; afterwards it is the case status. This keeps the 3B-2
    response contract stable while exposing the new workflow.
    """
    publication = None
    if session.current_result_version_id is not None:
        publication = db.scalar(
            select(SessionResultPublication).where(
                SessionResultPublication.result_version_id
                == session.current_result_version_id
            )
        )
    case = _case_for_session(db, session.session_id)
    official = _official_v1(db, session)
    window = review_window_end(official[1]) if official is not None else None
    if case is not None:
        status = case.status
    elif publication is not None:
        status = publication.state
    else:
        status = "PENDING" if is_ai_official(session) else "LEGACY"
    can_request = (
        official is not None
        and case is None
        and session.status != "in_progress"
        and _server_now(db) <= window
    )
    return {
        "review_status": status,
        "review_window_expires_at": window,
        "can_request_review": can_request,
    }


def _view(case):
    return {
        "review_request_id": case.review_request_id,
        "session_id": case.session_id,
        "learner_id": case.learner_id,
        "origin": case.origin,
        "status": case.status,
        "reason": case.reason,
        "base_result_version_id": case.base_result_version_id,
        "requested_at": case.requested_at,
        "window_expires_at": case.window_expires_at,
        "claimed_by": case.claimed_by,
        "claimed_at": case.claimed_at,
        "claim_expires_at": case.claim_expires_at,
        "resolved_by": case.resolved_by,
        "resolved_at": case.resolved_at,
        "resolution_note": case.resolution_note,
        "regraded_result_version_id": case.regraded_result_version_id,
        "revision": case.revision,
    }


def _user_view(case, publication_state=None):
    v2_state = {
        "APPROVED_PENDING_ANALYSIS": "ANALYSIS_PENDING",
        "ANALYSIS_FAILED": "ANALYSIS_FAILED_V1_KEPT",
        "OFFICIAL": "OFFICIAL",
    }.get(publication_state, "NONE")
    return UserReviewRequestView.model_validate({**_view(case), "v2_state": v2_state})


def _publication_state(case):
    return select(SessionResultPublication.state).where(
        SessionResultPublication.result_version_id == case.regraded_result_version_id
    ).scalar_subquery()


def _learner_identity(db, learner_id):
    account = db.get(Account, learner_id)
    if account is None:
        return learner_id, "", ""
    name = account.profile.full_name if account.profile else None
    return account.account_id, name or account.email, account.email


def _queue_item(db, case):
    _, name, email = _learner_identity(db, case.learner_id)
    session = db.get(AssessmentSession, case.session_id)
    return {
        **_view(case),
        "learner_name": name,
        "learner_email": email,
        "session_status": session.status if session is not None else "unknown",
    }


def detail(db, review_request_id):
    case = db.get(ReviewRequest, review_request_id)
    if case is None:
        raise AppError(404, "review_not_found", "Review request not found")
    item = _queue_item(db, case)
    session = db.get(AssessmentSession, case.session_id)
    version = db.get(SessionResultVersion, case.base_result_version_id)
    publication = db.scalar(
        select(SessionResultPublication).where(
            SessionResultPublication.result_version_id == case.base_result_version_id
        )
    )
    item.update(
        base_result_version=version.version_no if version is not None else None,
        base_publication=publication.state if publication is not None else None,
        published_at=publication.published_at if publication is not None else None,
        assessment_title=(session.config_snapshot or {}).get("title", "") if session is not None else "",
    )
    from ..models import QuestionReport, ReviewDeviation
    from .review_regrade import _deviation_view, _question_report_view
    item["question_reports"] = [
        _question_report_view(row) for row in db.scalars(
            select(QuestionReport)
            .where(QuestionReport.review_request_id == review_request_id)
            .order_by(QuestionReport.question_report_id))
    ]
    item["deviations"] = [
        _deviation_view(row) for row in db.scalars(
            select(ReviewDeviation)
            .where(ReviewDeviation.review_request_id == review_request_id)
            .order_by(ReviewDeviation.deviation_id))
    ]
    analysis_status = None
    if case.regraded_result_version_id is not None:
        regraded_publication = db.scalar(
            select(SessionResultPublication).where(
                SessionResultPublication.result_version_id
                == case.regraded_result_version_id)
        )
        analysis_status = (regraded_publication.state
                           if regraded_publication is not None else None)
    item["analysis_status"] = analysis_status
    return item


def request_review(db, session_id, learner, request_key: UUID, reason: str):
    """Create the one case for a session; 201 new, 200 idempotent replay."""
    text = (reason or "").strip()
    if len(text) < 10:
        raise AppError(422, "review_reason_required", "Provide a review reason of at least 10 characters")
    repo = AssessmentRepository(db)
    session = repo.lock_session(session_id)
    if session is None:
        raise AppError(404, "session_not_found", "Assessment session not found")
    if session.learner_id != learner.account_id:
        raise AppError(403, "review_forbidden", "Only the session owner can request a review")
    by_key = select(ReviewRequest, _publication_state(ReviewRequest)).where(ReviewRequest.request_key == request_key)
    existing_row = db.execute(by_key).one_or_none()
    if existing_row is not None:
        existing, publication_state = existing_row
        if existing.session_id != session_id or existing.requested_by != learner.account_id:
            raise AppError(
                409, "idempotency_conflict",
                "This Idempotency-Key belongs to another review request",
            )
        return 200, _user_view(existing, publication_state)
    current = _case_for_session(db, session_id)
    if current is not None:
        raise AppError(
            409, "review_exists",
            "A review request already exists for this session",
            details={"status": current.status, "revision": current.revision},
        )
    if not is_ai_official(session) or session.status == "in_progress":
        raise AppError(
            409, "review_not_eligible",
            "Only finalized FIXED TEST sessions with an official AI result can be reviewed",
        )
    official = _official_v1(db, session)
    if official is None:
        raise AppError(
            409, "review_not_eligible",
            "The official V1 result is not available yet",
        )
    version, publication = official
    window = review_window_end(publication)
    if repo.server_time() > window:
        raise AppError(
            409, "review_window_closed",
            "The review window for this result has closed",
            details={"window_expires_at": window.isoformat()},
        )
    case = ReviewRequest(
        session_id=session_id,
        learner_id=session.learner_id,
        requested_by=learner.account_id,
        origin="LEARNER",
        request_key=request_key,
        reason=text,
        status="REQUESTED",
        base_result_version_id=version.result_version_id,
    )
    db.add(case)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        replay_row = db.execute(by_key).one_or_none()
        if replay_row is not None:
            replay, publication_state = replay_row
            if replay.session_id == session_id and replay.requested_by == learner.account_id:
                return 200, _user_view(replay, publication_state)
        raced = _case_for_session(db, session_id)
        if raced is not None:
            raise AppError(
                409, "review_exists",
                "A review request already exists for this session",
                details={"status": raced.status, "revision": raced.revision},
            )
        raise AppError(409, "review_conflict", "The review request could not be created")
    db.refresh(case)
    payload = _user_view(case)
    db.commit()
    return 201, payload


def get_review(db, session_id, account):
    session = db.get(AssessmentSession, session_id)
    if session is None:
        raise AppError(404, "session_not_found", "Assessment session not found")
    is_owner = session.learner_id == account.account_id
    if not is_owner and not _is_admin(account):
        raise AppError(403, "review_forbidden", "Only the owner or an administrator can read this review")
    row = db.execute(select(ReviewRequest, _publication_state(ReviewRequest)).where(
        ReviewRequest.session_id == session_id
    )).one_or_none()
    if row is None:
        raise AppError(404, "review_not_found", "No review request exists for this session")
    case, publication_state = row
    if is_owner:
        return _user_view(case, publication_state)
    return ReviewRequestView.model_validate(_view(case))


def list_queue(db, *, status=None, limit=100, offset=0):
    if status is not None and status not in REVIEW_STATUSES:
        raise AppError(422, "invalid_review_status", "Unknown review status")
    stmt = select(ReviewRequest).order_by(
        ReviewRequest.created_at, ReviewRequest.review_request_id
    )
    if status is not None:
        stmt = stmt.where(ReviewRequest.status == status)
    return [_queue_item(db, row) for row in db.scalars(stmt.limit(limit).offset(offset))]


def _lock_case(db, review_request_id):
    return db.scalar(
        select(ReviewRequest)
        .where(ReviewRequest.review_request_id == review_request_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def _require_not_owner(db, case, admin):
    session = db.get(AssessmentSession, case.session_id)
    if session is not None and session.learner_id == admin.account_id:
        raise AppError(
            403, "self_review_forbidden",
            "An administrator cannot review their own assessment",
        )


def claim(db, review_request_id, expected_revision, admin):
    case = _lock_case(db, review_request_id)
    if case is None:
        raise AppError(404, "review_not_found", "Review request not found")
    _require_not_owner(db, case, admin)
    if case.revision != expected_revision:
        raise AppError(409, "review_conflict", "The review case changed. Reload it.")
    if case.status != "REQUESTED":
        raise AppError(
            409, "review_not_claimable",
            "Only a REQUESTED case can be claimed",
            details={"status": case.status},
        )
    now = _server_now(db)
    case.status = "IN_REVIEW"
    case.claimed_by = admin.account_id
    case.claimed_at = now
    case.claim_expires_at = now + timedelta(minutes=CLAIM_LEASE_MINUTES)
    db.flush()
    db.refresh(case)
    payload = detail(db, review_request_id)
    db.commit()
    return payload


def decide(db, review_request_id, expected_revision, outcome, note, admin):
    """REJECT only in this PR; APPROVE is reserved for 3B-5."""
    if outcome != "REJECT":
        raise AppError(422, "invalid_review_decision", "Only REJECT is available in this release")
    case = _lock_case(db, review_request_id)
    if case is None:
        raise AppError(404, "review_not_found", "Review request not found")
    _require_not_owner(db, case, admin)
    if case.revision != expected_revision:
        raise AppError(409, "review_conflict", "The review case changed. Reload it.")
    if case.status != "IN_REVIEW":
        raise AppError(
            409, "review_not_decidable",
            "The case must be claimed before a decision",
            details={"status": case.status},
        )
    if case.claimed_by != admin.account_id:
        raise AppError(
            409, "review_claim_required",
            "Only the administrator holding the claim can decide",
        )
    now = _server_now(db)
    if case.claim_expires_at is not None and case.claim_expires_at <= now:
        raise AppError(409, "review_claim_expired", "The claim lease expired; reload the queue")
    text = (note or "").strip()
    if len(text) < 10:
        raise AppError(422, "review_reason_required", "Provide a rejection reason of at least 10 characters")
    case.status = "REJECTED"
    case.resolved_by = admin.account_id
    case.resolved_at = now
    case.resolution_note = text
    db.flush()
    db.refresh(case)
    payload = detail(db, review_request_id)
    db.commit()
    return payload


def _recover_interrupted_analysis(db, case, now):
    if case.regraded_result_version_id is None:
        return
    publication = db.get(SessionResultPublication, case.regraded_result_version_id, populate_existing=True)
    if publication is None or publication.state != "APPROVED_PENDING_ANALYSIS":
        return
    run_ids = list(db.scalars(
        update(AiStageRun)
        .where(AiStageRun.result_version_id == publication.result_version_id,
               AiStageRun.run_mode == "V2_ANALYSIS", AiStageRun.status.in_(ACTIVE_STATUSES))
        .values(status="FAILED", last_error_code="analysis_interrupted", finished_at=now, lease_until=None)
        .returning(AiStageRun.stage_run_id)
    ))
    if run_ids:
        db.execute(
            update(AiStageAttempt)
            .where(AiStageAttempt.stage_run_id.in_(run_ids), AiStageAttempt.status == "STARTED")
            .values(status="FAILED", error_code="analysis_interrupted", finished_at=now)
        )
    publication.state = "ANALYSIS_FAILED"


def reclaim_and_expire(db, now=None):
    """Maintenance tick: expired leases return to REQUESTED; old cases expire.

    Interrupted analysis becomes retryable without changing the official result.
    """
    now = now or _server_now(db)
    reclaimed = 0
    expired_claim = and_(ReviewRequest.status == "IN_REVIEW", ReviewRequest.claim_expires_at <= now)
    # A previous worker version may have already reclaimed an interrupted case.
    abandoned = and_(ReviewRequest.status.in_(("REQUESTED", "EXPIRED")),
                     _publication_state(ReviewRequest) == "APPROVED_PENDING_ANALYSIS")
    for case in db.scalars(
        select(ReviewRequest)
        .where(or_(expired_claim, abandoned))
        .with_for_update(skip_locked=True)
        .execution_options(populate_existing=True)
    ):
        _recover_interrupted_analysis(db, case, now)
        if case.status != "IN_REVIEW":
            continue
        case.status = "REQUESTED"
        case.claimed_by = None
        case.claimed_at = None
        case.claim_expires_at = None
        reclaimed += 1
    if reclaimed:
        # autoflush is disabled for request sessions; the expiry scan below
        # must see the reclaimed status rather than the pre-lease snapshot.
        db.flush()
    cutoff = now - timedelta(days=CASE_TTL_DAYS)
    expired = 0
    for case in db.scalars(
        select(ReviewRequest)
        .where(
            ReviewRequest.status.in_(("REQUESTED", "IN_REVIEW")),
            ReviewRequest.created_at <= cutoff,
        )
        .with_for_update(skip_locked=True)
        .execution_options(populate_existing=True)
    ):
        case.status = "EXPIRED"
        case.claimed_by = None
        case.claimed_at = None
        case.claim_expires_at = None
        case.resolved_at = now
        expired += 1
    db.flush()
    return {"reclaimed": reclaimed, "expired": expired}
