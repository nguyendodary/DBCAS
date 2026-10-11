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


def list_learner_sessions(db: Session, learner: Account) -> list[SessionSummary]:
    """UC18 — the learner's sessions, newest first, with attempt counts."""
    return sessions_for_learner_id(db, learner.account_id)


def sessions_for_learner_id(db: Session, learner_id: int) -> list[SessionSummary]:
    """Shared by the learner endpoint and the admin drill-down."""
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
        final = s.status in {"completed", "timed_out"}
        items.append(
            SessionSummary(
                session_id=s.session_id,
                assessment_id=s.assessment_id,
                assessment_title=(s.config_snapshot or {}).get("title", s.assessment.title if s.assessment else ""),
                status=s.status,
                started_at=s.started_at,
                expires_at=s.expires_at,
                submitted_at=s.submitted_at,
                served_count=len(attempts),
                answered_count=len(submitted),
                graded_count=len(graded),
                pending_grading_count=sum(a.grading_status == "pending" for a in submitted),
                failed_grading_count=sum(a.grading_status == "failed" for a in submitted),
                overall_result_pct=(earned / possible * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if final and possible and len(graded) == len(submitted) else None,
                concepts=concept_items(s, _aggregate(graded), targets_for_session(s, CompetencyRepository(db))) if final else [],
            )
        )
    return items
