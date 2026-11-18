"""Published multi-assessment evidence; deterministic and provider independent."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from types import SimpleNamespace

from ..repositories import AssessmentRepository, CompetencyRepository
from .competency_service import _aggregate, category_display
from .evidence_context import concept_context, targets_for_session
from .grading_review import is_published
from .result_version import current_scores, is_ai_official

CENT = Decimal("0.01")


def is_test_evidence(session):
    """Only server-created TEST rows count; backfill is history-only."""
    return session.purpose == "TEST" and session.purpose_source == "SERVER"


def is_adaptive_estimate(session):
    snapshot = session.config_snapshot or {}
    return is_test_evidence(session) and (
        snapshot.get("result_kind") == "estimated_ability"
        and snapshot.get("runner_mode") == "adaptive"
    )


def is_official(session):
    """Table 1: published server TEST rows with an official percentage.

    Continuous adaptive rows go to the separate estimated-ability table.
    Formal adaptive sessions are intentionally in neither table in this PR.
    """
    snapshot = session.config_snapshot or {}
    official_pointer = (is_ai_official(session)
                        and getattr(session, "current_result_version_id", None) is not None)
    return (
        is_test_evidence(session)
        and (is_published(session) or official_pointer)
        and not is_adaptive_estimate(session)
        and snapshot.get("assembly_mode") != "ADAPTIVE"
    )


def is_pending_official(session):
    """Pending counterpart of table 1, used by dashboard counts."""
    snapshot = session.config_snapshot or {}
    return (
        is_test_evidence(session)
        and not is_published(session)
        and not is_adaptive_estimate(session)
        and snapshot.get("assembly_mode") != "ADAPTIVE"
    )


def aggregate_sessions(sessions, attempts_by_session, targets_by_session,
                       version_scores_by_session=None):
    """Pool point totals, not session percentages; keep evidence provenance.

    Repeated assessments count as separate observations without silently
    replacing earlier evidence. A multi-tag item contributes fully to each
    confirmed concept, following the established session scoring formula.
    Benchmarks are weighted by possible points where a target was defined.
    Only published server TEST rows are included, so learning-only PRACTICE
    sessions never enter official competency. AI-official sessions take their
    scores from the current result version; LEGACY sessions keep attempt.score.
    """
    totals = {}
    version_scores_by_session = version_scores_by_session or {}
    for session in sorted(sessions, key=lambda s: (s.started_at, s.session_id)):
        if not is_official(session):
            continue
        scores = version_scores_by_session.get(session.session_id) or {}
        if scores:
            evidence = []
            for attempt in attempts_by_session.get(session.session_id, []):
                if (attempt.submitted_at is None
                        or attempt.attempt_id not in scores):
                    continue
                scored = SimpleNamespace(**vars(attempt))
                scored.score = scores[attempt.attempt_id]
                evidence.append(scored)
        else:
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
    from ..schemas import (
        CumulativeAdaptiveItem,
        CumulativeCompetencyResult,
        CumulativeConceptItem,
        ProfileSummary,
    )
    from .continuous_adaptive import estimate

    repo = AssessmentRepository(db)
    all_sessions = repo.sessions_for_learner(learner_id)
    sessions = [s for s in all_sessions if is_official(s)]
    adaptive_sessions = [s for s in all_sessions
                         if is_adaptive_estimate(s) and is_published(s)]
    grouped = defaultdict(list)
    for attempt in repo.history_attempts(
        [s.session_id for s in sessions] + [s.session_id for s in adaptive_sessions]
    ):
        grouped[attempt.session_id].append(attempt)
    targets = {s.session_id: targets_for_session(s, CompetencyRepository(db)) for s in sessions}
    version_scores = {s.session_id: current_scores(db, s) for s in sessions}
    totals = aggregate_sessions(sessions, grouped, targets, version_scores)
    adaptive_estimates = []
    for session in adaptive_sessions:
        estimate_result = estimate(session, grouped.get(session.session_id, []))
        if estimate_result is None:
            continue
        adaptive_estimates.append(
            CumulativeAdaptiveItem(
                session_id=session.session_id,
                assessment_title=(session.config_snapshot or {}).get(
                    "title", session.assessment.title if session.assessment else ""
                ),
                started_at=session.started_at,
                submitted_at=session.submitted_at,
                band=estimate_result["band"],
                ability_index=estimate_result["index"],
                confidence=estimate_result["confidence"],
                evidence_count=estimate_result["evidence_count"],
            )
        )
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
        adaptive_estimates=adaptive_estimates,
        summary=ProfileSummary(assessed_concepts=len(items), benchmarked_concepts=len(benchmarked),
            meeting_target=sum(not i.below_target for i in benchmarked),
            unbenchmarked_concepts=len(items) - len(benchmarked), finalized_assessments=len(sessions)))
