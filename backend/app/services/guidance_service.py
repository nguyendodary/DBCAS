"""Personalized Study Guidance service — Task 5.2 (DBCAS-27).

Pipeline:

    competency profile (Task 4.1)
        + skill gaps (Task 4.2)
        + prerequisite skill graph (Task 5.1)
        -> prioritized "What to study next" guidance

The recommendations ARE the documented study list: below-benchmark concepts
ordered by shortfall (``target_pct - competency_pct``), now refined by the
prerequisite graph — a concept whose direct prerequisite is itself below
target is sequenced *after* that prerequisite instead of by raw shortfall.
Ranking is a deterministic topological sort over the induced gap subgraph;
among unblocked concepts the larger shortfall still wins, ``concept_id``
breaks ties.

Missing evidence stays distinct from low competency: an unassessed
prerequisite cannot gap and therefore never blocks a recommendation (FR-14;
unassessed ≠ failed). The assistive ``gap_explain`` LLM explanations carry
over from the gap report verbatim — they are attached after ranking and can
never influence order. Guidance is derived on read and never persisted, so
repeated requests are idempotent by construction.
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from ..models import Account, Concept
from ..repositories import CompetencyRepository, ConceptGraphRepository
from ..schemas import (
    GuidancePrerequisiteItem,
    StudyGuidanceItem,
    StudyGuidanceResult,
)
from . import competency_service
from .concept_graph_service import (
    edges_of,
    prerequisite_map,
    topological_order,
)
from .llm import LLMService

_CENT = Decimal("0.01")


def _prerequisite_status(
    prereq: Concept,
    competency,
    target_pct: Optional[Decimal],
) -> GuidancePrerequisiteItem:
    """Map a prerequisite's session evidence onto its guidance status.

    The documented mastery rule is the administrator-set benchmark: a
    measured concept below its target blocks ('below_target'), a measured
    concept not below target is 'satisfied', and no evidence row at all is
    'unassessed' — which never blocks (unassessed ≠ failed).
    """
    if competency is None:
        status = "unassessed"
        pct = None
    else:
        status = "below_target" if competency.below_target else "satisfied"
        pct = competency.competency_pct
    return GuidancePrerequisiteItem(
        concept_id=prereq.concept_id,
        concept_code=prereq.concept_code,
        concept_name=prereq.concept_name,
        status=status,
        competency_pct=pct,
        target_pct=target_pct,
    )


def _reason(
    shortfall: Decimal,
    target_pct: Decimal,
    blockers: list[str],
    unassessed: list[str],
) -> str:
    """Deterministic, factor-traceable explanation of a recommendation."""
    reason = f"{shortfall} pts below the {target_pct}% benchmark"
    if blockers:
        joined = ", ".join(f"'{name}' (below target)" for name in blockers)
        plural = "s" if len(blockers) > 1 else ""
        reason += f"; study prerequisite{plural} first: {joined}"
    elif unassessed:
        joined = ", ".join(f"'{name}'" for name in unassessed)
        plural = "s" if len(unassessed) > 1 else ""
        reason += f"; prerequisite{plural} not yet assessed: {joined}"
    return reason


def session_study_guidance(
    db: Session,
    session_id: int,
    learner: Account,
    llm: Optional[LLMService] = None,
) -> StudyGuidanceResult:
    """UC17 refinement — the learner's prioritized study guidance for a
    finalized session: gap concepts re-sequenced prerequisite-first.

    Delegates detection, ranking basis, and explanations to the Sprint 4 gap
    report so guidance can never diverge from it; then applies the skill
    graph to the ordering only.
    """
    report = competency_service.session_gap_report(
        db, session_id, learner, llm
    )
    if not report.gaps:
        return StudyGuidanceResult(
            session_id=report.session_id,
            assessment_id=report.assessment_id,
            status=report.status,
            guidance=[],
        )

    repo = CompetencyRepository(db)
    competency = {r.concept_id: r for r in repo.competencies_for_session(
        session_id
    )}
    targets = repo.assessment_targets(report.assessment_id)

    graph_repo = ConceptGraphRepository(db)
    edges = edges_of(graph_repo.all_edges())
    prereqs = prerequisite_map(edges)

    gap_by_id = {g.concept_id: g for g in report.gaps}
    order = topological_order(
        gap_by_id.keys(),
        edges,
        key=lambda cid: (-gap_by_id[cid].gap, cid),
    )

    needed = set()
    for cid in gap_by_id:
        needed |= prereqs.get(cid, set())
    concepts = {c.concept_id: c for c in graph_repo.get_concepts(needed)}

    items: list[StudyGuidanceItem] = []
    for priority, cid in enumerate(order, start=1):
        gap = gap_by_id[cid]
        blockers: list[str] = []
        unassessed: list[str] = []
        prereq_items: list[GuidancePrerequisiteItem] = []
        for pid in sorted(prereqs.get(cid, ())):
            prereq = concepts.get(pid)
            if prereq is None:
                continue  # edge points at a deleted concept — skip safely
            item = _prerequisite_status(
                prereq, competency.get(pid), targets.get(pid)
            )
            if item.status == "below_target":
                blockers.append(prereq.concept_name)
            elif item.status == "unassessed":
                unassessed.append(prereq.concept_name)
            prereq_items.append(item)
        items.append(
            StudyGuidanceItem(
                concept_id=cid,
                concept_code=gap.concept_code,
                concept_name=gap.concept_name,
                subject_area=gap.subject_area,
                description=gap.description,
                competency_pct=gap.competency_pct,
                target_pct=gap.target_pct,
                shortfall=gap.gap,
                priority=priority,
                ready=not blockers,
                prerequisites=prereq_items,
                reason=_reason(gap.gap, gap.target_pct, blockers, unassessed),
                contributing_attempts=gap.contributing_attempts,
                llm_explanation=gap.llm_explanation,
            )
        )
    return StudyGuidanceResult(
        session_id=report.session_id,
        assessment_id=report.assessment_id,
        status=report.status,
        guidance=items,
    )
