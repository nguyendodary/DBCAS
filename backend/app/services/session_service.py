"""Assessment session use cases — learner-facing lifecycle and history.

UC18 lists immutable per-concept results and submitted answer evidence.
"""

from sqlalchemy.orm import Session
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from ..models import Account
from ..repositories import AssessmentRepository, CompetencyRepository
from ..schemas import SessionSummary
from .evidence_context import question_view, targets_for_session
from .competency_service import _aggregate, concept_items
from .grading_review import is_published


def list_learner_sessions(db: Session, learner: Account) -> list[SessionSummary]:
    """UC18 — the learner's sessions, newest first, with attempt counts."""
    return sessions_for_learner_id(db, learner.account_id)


def sessions_for_learner_id(db: Session, learner_id: int) -> list[SessionSummary]:
    """Shared by the learner endpoint and the admin drill-down."""
    from .adaptive_engine import progress
    from .continuous_adaptive import estimate
    repo = AssessmentRepository(db)
    sessions = repo.sessions_for_learner(learner_id)
    grouped = defaultdict(list)
    for attempt in repo.history_attempts([s.session_id for s in sessions]):
        grouped[attempt.session_id].append(attempt)
    items = []
    for s in sessions:
        attempts = grouped[s.session_id]
        submitted = [a for a in attempts if a.submitted_at is not None]
        graded = [a for a in submitted if a.score is not None]
        possible = sum((question_view(a).points for a in graded), Decimal(0))
        earned = sum((a.score for a in graded), Decimal(0))
        practice = bool((s.config_snapshot or {}).get("learner_defined"))
        provisional = practice and not is_published(s) and s.release_status in ("provisional_ai", "pending_review")
        cancelled = s.status == "cancelled"
        final = is_published(s) or provisional
        adaptive = (s.config_snapshot or {}).get("runner_mode") == "adaptive"
        if cancelled:
            overall = Decimal("0")
        elif final and not adaptive and possible and len(graded) == len(submitted):
            overall = (earned / possible * 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            overall = None
        items.append(
            SessionSummary(
                session_id=s.session_id,
                assessment_id=s.assessment_id,
                assessment_title=(s.config_snapshot or {}).get("title", s.assessment.title if s.assessment else ""),
                status=s.status,
                locale=s.locale or "en",
                result_release_policy=s.result_release_policy, release_status=s.release_status,
                selected_concept_ids=(s.config_snapshot or {}).get("selected_concept_ids", []),
                difficulty=(s.config_snapshot or {}).get("difficulty"),
                assembly_mode=(s.config_snapshot or {}).get("assembly_mode"),
                runner_mode=(s.config_snapshot or {}).get("runner_mode"),
                result_kind=(s.config_snapshot or {}).get("result_kind"),
                adaptive_progress=progress(s, attempts),
                ability_estimate=estimate(s, attempts) if adaptive else None,
                started_at=s.started_at,
                expires_at=s.expires_at,
                submitted_at=s.submitted_at,
                served_count=len(attempts),
                answered_count=len(submitted),
                graded_count=len(graded),
                pending_grading_count=sum(a.grading_status == "pending" for a in submitted),
                failed_grading_count=sum(a.grading_status == "failed" for a in submitted),
                overall_result_pct=overall,
                concepts=[] if adaptive else (concept_items(s, _aggregate(graded), targets_for_session(s, CompetencyRepository(db))) if final else []),
                provisional=provisional,
                tab_leave_count=int(s.tab_leave_count or 0),
                cancelled_at=s.cancelled_at,
                cancel_reason=s.cancel_reason,
            )
        )
    return items
