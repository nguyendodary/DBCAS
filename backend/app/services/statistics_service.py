"""Read-only dashboard statistics derived from official published evidence."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from ..errors import AppError
from ..repositories import AccountRepository, AssessmentRepository, CompetencyRepository, StatisticsRepository
from .competency_dimensions import extract_evidence, metric, rank_learners, summarize
from .cumulative_competency import aggregate_sessions, is_official
from .evidence_context import targets_for_session

CENT = Decimal("0.01")


def _recommendations(db, sessions, attempts):
    repo = CompetencyRepository(db)
    targets = {s.session_id: targets_for_session(s, repo) for s in sessions}
    totals = aggregate_sessions(sessions, attempts, targets)
    topics = defaultdict(list)
    for cid, slot in totals.items():
        if not slot["target_possible"] or not slot["possible"]:
            continue
        target = slot["target_weight"] / slot["target_possible"]
        pct = slot["earned"] / slot["possible"] * 100
        gap = (target.quantize(CENT, rounding=ROUND_HALF_UP) - pct.quantize(CENT, rounding=ROUND_HALF_UP))
        if gap > 0:
            topics[slot["concept"].subject_area].append((gap, cid))
    items = [{"topic": topic, "concept_ids": [cid for gap, cid in sorted(gaps, key=lambda p: (-p[0], p[1]))],
              "maximum_shortfall_pct": max(gap for gap, _ in gaps)} for topic, gaps in topics.items()]
    items.sort(key=lambda item: (-item["maximum_shortfall_pct"], item["topic"]))
    return [{**item, "priority": index} for index, item in enumerate(items, 1)]


def dashboard(db, *, learner_id=None, assessment_id=None, include_ranking=False, limit=100, offset=0):
    if learner_id is not None:
        account = AccountRepository(db).get_with_roles(learner_id)
        if account is None or not any(r.role_name == "Learner" for r in account.roles):
            raise AppError(404, "learner_not_found", "Learner not found")
    if assessment_id is not None and AssessmentRepository(db).get_assessment(assessment_id) is None:
        raise AppError(404, "assessment_not_found", "Assessment not found")
    sessions = [s for s in StatisticsRepository(db).published_sessions(learner_id, assessment_id) if is_official(s)]
    attempts = defaultdict(list)
    for attempt in AssessmentRepository(db).history_attempts([s.session_id for s in sessions]):
        attempts[attempt.session_id].append(attempt)
    try:
        rows = extract_evidence(sessions, attempts)
    except (ValueError, ArithmeticError):
        raise AppError(500, "invalid_statistics_evidence", "Published score evidence requires administrator review") from None
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.session_id].append(row)
    progress = [{"session_id": s.session_id, "learner_id": s.learner_id,
                 "completed_at": s.submitted_at or s.published_at or s.started_at, **metric(grouped[s.session_id])}
                for s in sessions if grouped[s.session_id]]
    progress.sort(key=lambda p: (p["completed_at"], p["session_id"]))
    distribution = []
    for lower in range(0, 100, 20):
        upper = lower + 20
        count = sum(lower <= p["competency_pct"] and (p["competency_pct"] < upper or upper == 100)
                    for p in progress)
        distribution.append({"lower_bound": lower, "upper_bound": upper, "upper_inclusive": upper == 100, "count": count})
    return {"learner_id": learner_id, "assessment_id": assessment_id, "dimensions": summarize(rows),
            "published_formal_sessions": len(sessions), "graded_sessions": len(progress),
            "progress": progress[offset:offset + limit], "progress_total": len(progress), "limit": limit, "offset": offset,
            "score_distribution": distribution,
            "recommendations": _recommendations(db, sessions, attempts) if learner_id is not None else [],
            "ranking": rank_learners(rows) if include_ranking else []}
