"""Analytics service — UC20 / Admin story 9 (DBCAS-25).

The administrator dashboard reads the SAME deterministic concept_competency
records learners see; nothing is recomputed differently for the cohort.
Per-learner aggregation uses each learner's latest finalized session per
concept so resits cannot skew averages or below-benchmark rates.
"""

from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from ..errors import AppError
from ..repositories import AnalyticsRepository, AssessmentRepository
from ..schemas import (
    AdminLearnerItem,
    AdminLearnerSessionsResult,
    CohortConceptStat,
    CohortOverviewResult,
    CompetencyProfileResult,
)
from . import competency_service, session_service
from .session_guard import load_finalized_session

_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _backfill_competency(db: Session, repo: AnalyticsRepository,
                         assessment_id: int | None) -> None:
    """Persist competency rows for finalized sessions that have evidence
    but were never opened through a results endpoint.

    Finalization normally computes these rows; a session finalized only by
    expiry still needs them so the cohort view is complete. Uses the same
    deterministic compute as the learner path — identical input, identical
    output.
    """
    sessions = repo.finalized_sessions(assessment_id)
    missing = set(
        repo.sessions_missing_competency([s.session_id for s in sessions])
    )
    for session in sessions:
        if session.session_id in missing:
            competency_service.compute_session_competency(db, session)


def _stat(row) -> CohortConceptStat:
    assessed = int(row.learners_assessed)
    below = int(row.below or 0)
    avg = Decimal(str(row.avg_pct or 0)).quantize(_CENT, rounding=ROUND_HALF_UP)
    rate = (
        (Decimal(below) / Decimal(assessed) * _HUNDRED).quantize(
            _CENT, rounding=ROUND_HALF_UP
        )
        if assessed
        else Decimal("0")
    )
    return CohortConceptStat(
        concept_id=row.concept_id,
        concept_code=row.concept_code,
        concept_name=row.concept_name,
        subject_area=row.subject_area,
        learners_assessed=assessed,
        avg_competency_pct=avg,
        below_target_count=below,
        gap_rate_pct=rate,
    )


def cohort_overview(db: Session, assessment_id: int | None) -> CohortOverviewResult:
    """UC20 — cohort-wide competency + below-benchmark prevalence.

    Optional ``assessment_id`` scopes the whole view to one configuration,
    matching 'selects a learner or a cohort and an assessment'.
    """
    repo = AnalyticsRepository(db)
    if assessment_id is not None and repo.get_assessment(assessment_id) is None:
        raise AppError(404, "assessment_not_found", "Assessment not found")
    _backfill_competency(db, repo, assessment_id)
    learners, sessions = repo.cohort_counts(assessment_id)
    stats = sorted(
        (_stat(r) for r in repo.cohort_concept_stats(assessment_id)),
        key=lambda s: (-s.gap_rate_pct, -s.below_target_count, s.concept_id),
    )
    weakest = [s for s in stats if s.below_target_count > 0][:5]
    return CohortOverviewResult(
        learner_count=learners,
        finalized_sessions=sessions,
        concepts=stats,
        weakest_concepts=weakest,
    )


def list_learners(db: Session) -> list[AdminLearnerItem]:
    """Roster for the admin 'select a learner' step."""
    return [
        AdminLearnerItem(
            account_id=row.account_id,
            email=row.email,
            full_name=row.full_name,
            sessions_total=int(row.total or 0),
            sessions_completed=int(row.finalized or 0),
            last_activity=row.last_activity,
        )
        for row in AnalyticsRepository(db).learner_accounts()
    ]


def learner_sessions(db: Session, account_id: int) -> AdminLearnerSessionsResult:
    """One learner's assessment history (404 for unknown/non-learner ids)."""
    account = AnalyticsRepository(db).get_learner_account(account_id)
    if account is None:
        raise AppError(404, "learner_not_found", "Learner not found")
    return AdminLearnerSessionsResult(
        account_id=account.account_id,
        email=account.email,
        full_name=account.profile.full_name if account.profile else None,
        sessions=session_service.sessions_for_learner_id(db, account_id),
    )


def session_competency(db: Session, session_id: int) -> CompetencyProfileResult:
    """Admin-scoped competency read for any finalized session.

    Same finalization semantics as the learner path (expired sessions flip
    to timed_out once, still-running sessions conflict with 409); only the
    ownership rule differs.
    """
    session = load_finalized_session(AssessmentRepository(db), session_id)
    return competency_service.profile_for_session(db, session)
