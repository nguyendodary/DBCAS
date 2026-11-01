"""Deterministic point-weighted CLO/topic/difficulty metrics from published evidence."""
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from .cumulative_competency import is_official
from .evidence_context import question_view
from .grading_review import is_published

CENT = Decimal("0.01")
ZERO = Decimal(0)


@dataclass(frozen=True)
class Evidence:
    attempt_id: int
    session_id: int
    learner_id: int
    earned: Decimal
    possible: Decimal
    difficulty: int
    topics: tuple[str, ...]
    clos: tuple[tuple[str, str], ...]
    clo_mapping_known: bool

    def __post_init__(self):
        if (not self.earned.is_finite() or not self.possible.is_finite()
                or self.possible <= 0 or not ZERO <= self.earned <= self.possible
                or not 1 <= self.difficulty <= 5):
            raise ValueError("Invalid competency evidence")


def extract_evidence(sessions, attempts_by_session):
    rows = []
    for session in sessions:
        if not is_published(session) or not is_official(session):
            continue
        for attempt in attempts_by_session.get(session.session_id, []):
            if attempt.submitted_at is None or attempt.score is None or attempt.grading_status != "graded":
                continue
            question = question_view(attempt)
            if question.points <= 0:
                continue
            snapshot = attempt.question_snapshot or {}
            clos = {(str(c["clo_id"]), c["clo_code"] + " — " + c["title"])
                    for c in snapshot.get("clo_mappings", [])}
            topics = {tag.concept.subject_area for tag in question.concept_tags if tag.confirmed}
            rows.append(Evidence(attempt.attempt_id, session.session_id, session.learner_id,
                                 Decimal(str(attempt.score)), Decimal(str(question.points)),
                                 question.difficulty_level, tuple(sorted(topics)), tuple(sorted(clos)),
                                 "clo_mappings" in snapshot))
    return unique_evidence(rows)


def unique_evidence(rows):
    indexed = {}
    for row in rows:
        if row.attempt_id in indexed and indexed[row.attempt_id] != row:
            raise ValueError("Conflicting duplicated competency evidence")
        indexed[row.attempt_id] = row
    return [indexed[key] for key in sorted(indexed)]


def metric(rows):
    rows = unique_evidence(rows)
    earned = sum((r.earned for r in rows), ZERO)
    possible = sum((r.possible for r in rows), ZERO)
    return {"points_earned": earned, "points_possible": possible,
            "competency_pct": (earned / possible * 100).quantize(CENT, rounding=ROUND_HALF_UP) if possible else None,
            "evidence_count": len(rows)}


def summarize(rows):
    rows = unique_evidence(rows)
    dimensions = {}
    selectors = {"clos": lambda r: r.clos,
                 "topics": lambda r: tuple((t, t) for t in set(r.topics)) or (("unclassified", "Unclassified"),),
                 "difficulties": lambda r: ((str(r.difficulty), str(r.difficulty)),)}
    for dimension, selector in selectors.items():
        grouped, labels = defaultdict(list), {}
        for row in rows:
            for key, label in dict(selector(row)).items():
                grouped[key].append(row)
                labels[key] = label
        items = [{"key": key, "label": labels[key], **metric(values)} for key, values in grouped.items()]
        items.sort(key=lambda item: (-item["competency_pct"], item["key"]))
        rank, previous = 0, None
        for item in items:
            if item["competency_pct"] != previous:
                rank += 1
            item["rank"] = rank
            previous = item["competency_pct"]
        dimensions[dimension] = items
    return {"overall": metric(rows), **dimensions,
            "clo_mapping_unknown_attempts": sum(not r.clo_mapping_known for r in rows)}


def rank_learners(rows):
    grouped = defaultdict(list)
    for row in unique_evidence(rows):
        grouped[row.learner_id].append(row)
    items = [{"learner_id": key, **metric(values)} for key, values in grouped.items()]
    items.sort(key=lambda item: (-item["competency_pct"], item["learner_id"]))
    rank, previous = 0, None
    for position, item in enumerate(items, 1):
        if item["competency_pct"] != previous:
            rank = position
        item["rank"] = rank
        previous = item["competency_pct"]
    return items
