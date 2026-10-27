"""Published multi-assessment evidence; deterministic and provider independent."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from ..repositories import AssessmentRepository, CompetencyRepository
from .competency_service import _aggregate, category_display
from .evidence_context import concept_context, targets_for_session
from .grading_review import is_published

CENT = Decimal("0.01")


def is_official(session):
    """Practice runs are learning evidence and never official competency.

    Legacy sessions without an assembly mode retain their historical formal
    treatment; explicit PRACTICE and ADAPTIVE selections are excluded.
    """
    return (session.config_snapshot or {}).get("assembly_mode") not in ("PRACTICE", "ADAPTIVE")


def aggregate_sessions(sessions, attempts_by_session, targets_by_session):
    """Pool point totals, not session percentages; keep evidence provenance.

    Repeated assessments count as separate observations without silently
    replacing earlier evidence. A multi-tag item contributes fully to each
    confirmed concept, following the established session scoring formula.
    Benchmarks are weighted by possible points where a target was defined.
    Practice sessions are excluded so practice scores never enter official
    competency.
    """
    totals = {}
    for session in sorted(sessions, key=lambda s: (s.started_at, s.session_id)):
        if not is_published(session) or not is_official(session):
            continue
        evidence = [a for a in attempts_by_session.get(session.session_id, [])
                    if a.submitted_at is not None and a.score is not None
                    and a.grading_status == "graded"]
        agg = _aggregate(evidence)
        targets = targets_by_session.get(session.session_id, {})
        for cid, item in agg.items():
            if item["possible"] <= 0:
                continue
            slot = totals.setdefault(cid, {"earned": Decimal(0), "possible": Decimal(0),
                "target_weight": Decimal(0), "target_possible": Decimal(0),
                "attempt_ids": [], "session_ids": [], "below_count": 0, "meeting_count": 0})
            slot["earned"] += item["earned"]
            slot["possible"] += item["possible"]
            slot["attempt_ids"].extend(item["attempt_ids"])
            slot["session_ids"].append(session.session_id)
            # Latest published immutable context provides the display label;
            # prior attempt snapshots remain available in their own histories.
            slot["concept"] = concept_context(session, item["concept"])
            target = targets.get(cid)
            if target is not None:
                slot["target_weight"] += item["possible"] * target
                slot["target_possible"] += item["possible"]
                pct = (item["earned"] / item["possible"] * 100).quantize(CENT, rounding=ROUND_HALF_UP)
                slot["below_count"] += int(pct < target)
                slot["meeting_count"] += int(pct >= target)
    return totals


def profile(db, learner_id):
    from ..schemas import CumulativeCompetencyResult, CumulativeConceptItem, ProfileSummary
    repo = AssessmentRepository(db)
    sessions = [s for s in repo.sessions_for_learner(learner_id)
                if is_published(s) and is_official(s)]
    grouped = defaultdict(list)
    for attempt in repo.history_attempts([s.session_id for s in sessions]):
        grouped[attempt.session_id].append(attempt)
    targets = {s.session_id: targets_for_session(s, CompetencyRepository(db)) for s in sessions}
    totals = aggregate_sessions(sessions, grouped, targets)
    items = []
    for cid, slot in sorted(totals.items()):
        c = slot["concept"]
        pct = (slot["earned"] / slot["possible"] * 100).quantize(CENT, rounding=ROUND_HALF_UP)
        target = (slot["target_weight"] / slot["target_possible"]).quantize(CENT, rounding=ROUND_HALF_UP) if slot["target_possible"] else None
        items.append(CumulativeConceptItem(concept_id=cid, concept_code=c.concept_code,
            concept_name=c.concept_name, subject_area=c.subject_area,
            points_earned=slot["earned"], points_possible=slot["possible"], competency_pct=pct,
            target_pct=target, below_target=target is not None and pct < target,
            contributing_attempts=slot["attempt_ids"], contributing_sessions=slot["session_ids"],
            below_target_assessments=slot["below_count"], meeting_target_assessments=slot["meeting_count"]))
    benchmarked = [i for i in items if i.target_pct is not None]
    gaps = sorted([i for i in items if i.below_target], key=lambda i: (-(i.target_pct - i.competency_pct), i.concept_id))
    return CumulativeCompetencyResult(learner_id=learner_id, concepts=items, gaps=gaps,
        categories=category_display(items),
        summary=ProfileSummary(assessed_concepts=len(items), benchmarked_concepts=len(benchmarked),
            meeting_target=sum(not i.below_target for i in benchmarked),
            unbenchmarked_concepts=len(items) - len(benchmarked), finalized_assessments=len(sessions)))
