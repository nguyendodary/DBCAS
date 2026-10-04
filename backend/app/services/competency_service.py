"""Competency & Gap Service — deterministic per-concept scoring.

Pipeline position: the grading services (Sprints 2–3) persist a validated
``attempt.score`` plus ``grading_detail`` evidence per answer. This service
aggregates that evidence into one ``concept_competency`` row per
(session, concept) — it never re-grades MCQ/SQL/essay answers and never
lets LLM output feed the math.

Documented formula (Database Design Table 19; Proposal §12.4; UC16/FR-12):

    competency_pct = points_earned / points_possible × 100   (2 dp, HALF_UP)
    below_target   = competency_pct < assessment_concept.target_pct

* points_earned   = Σ attempt.score over the session's graded attempts whose
                    question is tagged to the concept
* points_possible = Σ question.points over those same attempts
* a question tagged to several concepts contributes its score fully to each
  (``question_concept`` is a junction table — it has no per-tag weight)
* a served-but-unsubmitted attempt is not evidence: it counts toward
  neither side of the ratio, and a concept with no evidence gets no row
  (unassessed ≠ failed)
* only the administrator-set ``target_pct`` produces a below_target flag;
  non-targeted concepts are still reported (the radar shows them) but can
  never be flagged

Recompute is idempotent: identical evidence rewrites identical values via
upsert on (session_id, concept_id), and stale rows are removed.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from ..models import Account, AssessmentSession, Attempt, ConceptCompetency
from ..repositories import AssessmentRepository, CompetencyRepository
from ..schemas import CompetencyProfileResult, ConceptCompetencyItem
from .session_guard import load_owned_finalized_session

logger = logging.getLogger(__name__)

_CENT = Decimal("0.01")
_ZERO = Decimal("0")
_HUNDRED = Decimal("100")


def _aggregate(attempts: list[Attempt]) -> dict[int, dict]:
    """Fold graded attempts into per-concept totals.

    Returns ``{concept_id: {"earned", "possible", "attempt_ids"}}`` — the
    attempt id list keeps every score traceable back to its evidence row.
    """
    agg: dict[int, dict] = {}
    for attempt in attempts:
        question = attempt.question
        if question is None or question.points is None:
            continue  # malformed evidence — skip, never crash the pipeline
        score = attempt.score or _ZERO
        for tag in question.concept_tags:
            slot = agg.setdefault(
                tag.concept_id,
                {"earned": _ZERO, "possible": _ZERO, "attempt_ids": []},
            )
            slot["earned"] += score
            slot["possible"] += question.points
            slot["attempt_ids"].append(attempt.attempt_id)
    return agg


def _persist_results(
    db: Session,
    repo: CompetencyRepository,
    session: AssessmentSession,
    agg: dict[int, dict],
) -> list[ConceptCompetency]:
    """Upsert the aggregate as concept_competency rows and commit."""
    targets = repo.assessment_targets(session.assessment_id)
    rows: list[ConceptCompetency] = []
    keep: set[int] = set()
    for concept_id in sorted(agg):
        possible = agg[concept_id]["possible"]
        if possible <= _ZERO:
            continue  # zero possible points means no real evidence
        earned = agg[concept_id]["earned"]
        pct = (earned / possible * _HUNDRED).quantize(_CENT, rounding=ROUND_HALF_UP)
        pct = max(_ZERO, min(pct, _HUNDRED))  # defensive clamp to the 0–100 scale
        target = targets.get(concept_id)
        rows.append(
            repo.upsert_competency(
                session.session_id,
                concept_id,
                points_earned=earned.quantize(_CENT),
                points_possible=possible.quantize(_CENT),
                competency_pct=pct,
                below_target=pct < target if target is not None else False,
            )
        )
        keep.add(concept_id)
    repo.delete_stale_competencies(session.session_id, keep)
    db.commit()
    return rows


def compute_session_competency(
    db: Session, session: AssessmentSession
) -> list[ConceptCompetency]:
    """(Re)compute and persist one session's per-concept competency.

    Called when a session becomes final (UC21 step 5: 'the session ends ...
    the system then computes competency') and on result reads, so a later
    finalization flow reuses this same entry point.
    """
    repo = CompetencyRepository(db)
    evidence = repo.session_evidence(session.session_id)
    return _persist_results(db, repo, session, _aggregate(evidence))


def session_competency_profile(
    db: Session, session_id: int, learner: Account
) -> CompetencyProfileResult:
    """UC16 — the learner's per-concept profile for their finalized session."""
    session = load_owned_finalized_session(
        AssessmentRepository(db), session_id, learner
    )
    repo = CompetencyRepository(db)
    agg = _aggregate(repo.session_evidence(session_id))
    rows = _persist_results(db, repo, session, agg)
    targets = repo.assessment_targets(session.assessment_id)
    items = [
        ConceptCompetencyItem(
            concept_id=row.concept_id,
            concept_code=row.concept.concept_code,
            concept_name=row.concept.concept_name,
            subject_area=row.concept.subject_area,
            points_earned=row.points_earned,
            points_possible=row.points_possible,
            competency_pct=row.competency_pct,
            target_pct=targets.get(row.concept_id),
            below_target=row.below_target,
            contributing_attempts=agg.get(row.concept_id, {}).get("attempt_ids", []),
        )
        for row in rows
    ]
    return CompetencyProfileResult(
        session_id=session.session_id,
        assessment_id=session.assessment_id,
        status=session.status,
        concepts=items,
    )
