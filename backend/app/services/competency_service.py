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
import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session

from ..models import (
    Account,
    AssessmentSession,
    Attempt,
    CompetencyGap,
    ConceptCompetency,
)
from ..repositories import AssessmentRepository, CompetencyRepository, AnalyticsRepository
from ..schemas import (
    CompetencyGapItem,
    CompetencyGapResult,
    CompetencyProfileResult,
    ConceptCompetencyItem,
    CompetencyCategory,
    ProfileSummary,
)
from .llm import ChatMessage, LLMError, LLMService
from .evidence_context import question_view, targets_for_session, concept_context
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
        question = question_view(attempt)
        if question is None or question.points is None:
            continue  # malformed evidence — skip, never crash the pipeline
        score = attempt.score or _ZERO
        for tag in question.concept_tags:
            if not tag.confirmed:
                continue
            slot = agg.setdefault(
                tag.concept_id,
                {"earned": _ZERO, "possible": _ZERO, "attempt_ids": [], "concept": tag.concept},
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
    """Write only changed aggregates; unchanged report reads remain reads."""
    targets = targets_for_session(session, repo)
    existing = {r.concept_id: r for r in repo.competencies_for_session(session.session_id)}
    rows: list[ConceptCompetency] = []
    keep: set[int] = set()
    changed = False
    for concept_id in sorted(agg):
        possible = agg[concept_id]["possible"]
        if possible <= _ZERO:
            continue  # zero possible points means no real evidence
        earned = agg[concept_id]["earned"]
        pct = (earned / possible * _HUNDRED).quantize(_CENT, rounding=ROUND_HALF_UP)
        pct = max(_ZERO, min(pct, _HUNDRED)).quantize(_CENT)  # keep the wire scale stable at 0/100
        target = targets.get(concept_id)
        previous = existing.get(concept_id)
        below = pct < target if target is not None else False
        if previous is not None and (
            previous.points_earned, previous.points_possible, previous.competency_pct, previous.below_target
        ) == (earned.quantize(_CENT), possible.quantize(_CENT), pct, below):
            rows.append(previous)
            keep.add(concept_id)
            continue
        changed = True
        rows.append(
            repo.upsert_competency(
                session.session_id,
                concept_id,
                points_earned=earned.quantize(_CENT),
                points_possible=possible.quantize(_CENT),
                competency_pct=pct,
                below_target=below,
            )
        )
        keep.add(concept_id)
    if set(existing) - keep:
        repo.delete_stale_competencies(session.session_id, keep)
        changed = True
    if changed:
        db.commit()
    return rows


def concept_items(session, agg, targets):
    """Decorate immutable evidence without writes (also used by history)."""
    items = []
    for cid in sorted(agg):
        slot = agg[cid]
        if slot["possible"] <= 0:
            continue
        concept = concept_context(session, slot["concept"])
        pct = (slot["earned"] / slot["possible"] * _HUNDRED).quantize(_CENT, rounding=ROUND_HALF_UP)
        target = targets.get(cid)
        items.append(ConceptCompetencyItem(concept_id=cid, concept_code=concept.concept_code,
            concept_name=concept.concept_name, subject_area=concept.subject_area,
            points_earned=slot["earned"], points_possible=slot["possible"], competency_pct=pct,
            target_pct=target, below_target=target is not None and pct < target,
            contributing_attempts=slot["attempt_ids"]))
    return items


def category_display(items):
    """FR-13 supplies no category formula: label this display aggregation."""
    result = []
    for area in sorted({i.subject_area for i in items}):
        group = [i for i in items if i.subject_area == area]
        targets = [i.target_pct for i in group if i.target_pct is not None]
        result.append(CompetencyCategory(subject_area=area, assessed_concepts=len(group),
            benchmarked_concepts=len(targets),
            mean_competency_pct=(sum(i.competency_pct for i in group) / len(group)).quantize(_CENT, rounding=ROUND_HALF_UP),
            mean_target_pct=(sum(targets) / len(targets)).quantize(_CENT, rounding=ROUND_HALF_UP) if targets else None))
    return result


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
    return profile_for_session(db, session)


def profile_for_session(
    db: Session, session: AssessmentSession
) -> CompetencyProfileResult:
    """Build the per-concept profile for an already-guarded session.

    Shared by the learner-facing endpoint and the admin analytics
    drill-down; the caller owns the access checks.
    """
    repo = CompetencyRepository(db)
    agg = _aggregate(repo.session_evidence(session.session_id))
    _persist_results(db, repo, session, agg)
    targets = targets_for_session(session, repo)
    items = concept_items(session, agg, targets)
    benchmarked = [i for i in items if i.target_pct is not None]
    return CompetencyProfileResult(
        session_id=session.session_id,
        assessment_id=session.assessment_id,
        status=session.status,
        concepts=items,
        categories=category_display(items),
        summary=ProfileSummary(assessed_concepts=len(items), benchmarked_concepts=len(benchmarked),
            meeting_target=sum(not i.below_target for i in benchmarked),
            unbenchmarked_concepts=len(items) - len(benchmarked),
            finalized_assessments=AnalyticsRepository(db).finalized_count_for_learner(session.learner_id)),
    )


# ---------- gap detection (Task 4.2 / FR-14, UC17) ----------
#
# A competency gap = a concept whose competency_pct is strictly below the
# assessment's administrator-set target_pct for it (``below_target`` on the
# competency row). Only targeted concepts can gap; a concept with no graded
# evidence has no competency row and is never auto-flagged. Gap DETECTION
# stands on benchmark shortfall alone — the prerequisite graph only affects
# readiness information produced by the guidance service, never detection or
# ranking.
#
# The "What to study next" list is derived — ordered by (target_pct -
# competency_pct) descending — and deliberately not stored (DB design).
# ``competency_gap.llm_explanation`` carries the assistive, evidence-linked
# plain-language explanation; it can never change scores or ranking.

GAP_EXPLAIN_SCHEMA = {
    "name": "gap_explanation",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {"explanation": {"type": "string", "minLength": 1}},
        "required": ["explanation"],
        "additionalProperties": False,
    },
}

_GAP_SYSTEM_PROMPT = (
    "You are a database course tutor writing a short diagnostic explanation "
    "for a learner's weak concept. Use only the supplied evidence: the "
    "concept, the benchmark, and per-question grading outcomes. Never invent "
    "questions or scores, never reveal expected answers, keep it under four "
    "plain sentences. Output JSON only."
)


def _evidence_summary(attempts: list[Attempt]) -> list[str]:
    """Whitelisted per-question outcome lines for the gap_explain prompt.

    Only grading outcomes and question metadata are sent — never learner
    answer text, never expected results or setup SQL (NFR-07 / FR-11).
    """
    lines = []
    for attempt in attempts:
        question = question_view(attempt)
        detail = attempt.grading_detail or {}
        earned = detail.get("points_earned", str(attempt.score))
        possible = detail.get("points_possible", str(question.points))
        line = (
            f"- {question.question_type} question "
            f"(difficulty {question.difficulty_level}): "
            f"{earned}/{possible} pts"
        )
        if question.question_type == "sql":
            line += (
                f" — {detail.get('status', 'unknown')}, "
                f"{detail.get('datasets_passed', '?')}/"
                f"{detail.get('datasets_total', '?')} test datasets passed"
            )
            missing = detail.get("missing_required_concepts") or []
            if missing:
                line += f", missing required technique: {', '.join(missing)}"
        elif question.question_type == "mcq":
            line += " — " + ("correct" if detail.get("is_correct") else "incorrect")
        elif question.question_type == "essay":
            line += f" — rubric level: {detail.get('rubric_level', 'unknown')}"
            missing = detail.get("missing_concepts") or []
            if missing:
                line += f", missing: {', '.join(missing)}"
        lines.append(line)
    return lines


def _explain_gap(
    llm: LLMService,
    concept,
    competency: ConceptCompetency,
    target_pct: Decimal,
    evidence_lines: list[str],
) -> Optional[str]:
    """One ``gap_explain`` structured call (cached by request hash).

    Any provider or validation failure returns None — the gap is still
    reported; the explanation is assistive and optional by design.
    """
    gap_amount = (target_pct - competency.competency_pct).quantize(_CENT)
    user_prompt = (
        f"CONCEPT: {concept.concept_name} ({concept.concept_code}) — "
        f"subject area: {concept.subject_area}\n"
        f"DESCRIPTION: {concept.description or '(none)'}\n"
        f"RESULT: {competency.competency_pct}% vs benchmark {target_pct}% "
        f"(shortfall {gap_amount} points)\n"
        "GRADING EVIDENCE FROM THIS SESSION:\n"
        + ("\n".join(evidence_lines) if evidence_lines else "- (none)")
        + '\n\nReturn JSON: {"explanation": "..."}'
    )
    try:
        def validate_explanation(value):
            text = value.get("explanation")
            if not isinstance(text, str) or not text.strip():
                raise LLMError(LLMError.INVALID_RESPONSE, "Empty gap explanation")
            return {"explanation": text.strip()}

        result = llm.generate_structured(
            "gap_explain",
            [
                ChatMessage("system", _GAP_SYSTEM_PROMPT),
                ChatMessage("user", user_prompt),
            ],
            json_schema=GAP_EXPLAIN_SCHEMA,
            validator=validate_explanation,
            context_version="gap-explanation-v2",
        )
    except LLMError as exc:
        logger.info("gap_explain skipped for concept %s: %s", concept.concept_id, exc.code)
        return None
    text = result.get("explanation") if isinstance(result, dict) else None
    if not isinstance(text, str) or not text.strip():
        return None  # malformed payload — leave NULL rather than store junk
    return text.strip()


def _sync_gaps(
    db: Session,
    repo: CompetencyRepository,
    session: AssessmentSession,
    competency_rows: list[ConceptCompetency],
) -> list[CompetencyGap]:
    """Sync competency_gap rows to the current below_target set.

    Existing status is preserved. Explanations survive only while their
    evidence and benchmark context stays identical; changed context clears
    them before a report can present them as current.
    """
    gaps: list[CompetencyGap] = []
    keep: set[int] = set()
    existing = {g.concept_id: g for g in repo.gaps_for_session(session.session_id)}
    changed = False
    targets = targets_for_session(session, repo)
    evidence = repo.session_evidence(session.session_id)
    agg = _aggregate(evidence)
    for row in competency_rows:
        if row.below_target:
            gap = existing.get(row.concept_id)
            if gap is None:
                gap = repo.upsert_gap(session.session_id, row.concept_id)
                changed = True
            ids = set(agg.get(row.concept_id, {}).get("attempt_ids", []))
            concept = concept_context(session, row.concept)
            context = {
                "version": 1,
                "concept": {"id": row.concept_id, "code": concept.concept_code,
                            "name": concept.concept_name,
                            "description": concept.description,
                            "subject_area": concept.subject_area},
                "competency": str(row.competency_pct.quantize(_CENT)),
                "target": str(targets[row.concept_id].quantize(_CENT)),
                "evidence": [
                    {"id": a.attempt_id, "score": str(a.score.quantize(_CENT)),
                     "points": str(question_view(a).points.quantize(_CENT)), "detail": a.grading_detail}
                    for a in sorted(evidence, key=lambda a: a.attempt_id)
                    if a.attempt_id in ids
                ],
            }
            digest = hashlib.sha256(json.dumps(context, sort_keys=True, default=str).encode()).hexdigest()
            if gap.explanation_context_hash != digest:
                gap.llm_explanation = None
                gap.explanation_context_hash = digest
                changed = True
            gaps.append(gap)
            keep.add(row.concept_id)
    if set(existing) - keep:
        repo.delete_stale_gaps(session.session_id, keep)
        changed = True
    if changed:
        db.commit()
    return gaps


def detect_session_gaps(
    db: Session, session: AssessmentSession
) -> list[CompetencyGap]:
    """(Re)compute competency, then refresh this session's gap records.

    Deterministic — safe to call on every report read and from the future
    session-finalization flow.
    """
    repo = CompetencyRepository(db)
    rows = compute_session_competency(db, session)
    return _sync_gaps(db, repo, session, rows)


def session_gap_report(
    db: Session,
    session_id: int,
    learner: Account,
    llm: Optional[LLMService] = None,
) -> CompetencyGapResult:
    """UC17 — below-benchmark concepts ranked by shortfall from target.

    The ordered ``gaps`` list IS the documented "What to study next" list;
    ranking is fixed before any explanation is attached, so LLM output can
    never affect scores or order.
    """
    session = load_owned_finalized_session(
        AssessmentRepository(db), session_id, learner
    )
    repo = CompetencyRepository(db)
    evidence = repo.session_evidence(session_id)
    agg = _aggregate(evidence)
    rows = _persist_results(db, repo, session, agg)
    targets = targets_for_session(session, repo)

    gaps = _sync_gaps(db, repo, session, rows)
    below = {r.concept_id: r for r in rows if r.below_target}
    by_attempt = {a.attempt_id: a for a in evidence}

    if llm is not None:
        changed = False
        for gap in gaps:
            if gap.llm_explanation is None:
                comp = below[gap.concept_id]
                attempts = [
                    by_attempt[i]
                    for i in agg[gap.concept_id]["attempt_ids"]
                    if i in by_attempt
                ]
                text = _explain_gap(
                    llm, concept_context(session, gap.concept), comp, targets[gap.concept_id],
                    _evidence_summary(attempts),
                )
                if text is not None:
                    gap.llm_explanation = text
                    changed = True
        if changed:
            db.commit()

    items = [
        CompetencyGapItem(
            concept_id=gap.concept_id,
            concept_code=concept_context(session, gap.concept).concept_code,
            concept_name=concept_context(session, gap.concept).concept_name,
            subject_area=concept_context(session, gap.concept).subject_area,
            description=concept_context(session, gap.concept).description,
            competency_pct=below[gap.concept_id].competency_pct,
            target_pct=targets[gap.concept_id],
            gap=(
                targets[gap.concept_id] - below[gap.concept_id].competency_pct
            ).quantize(_CENT),
            contributing_attempts=agg[gap.concept_id]["attempt_ids"],
            status=gap.status,
            llm_explanation=gap.llm_explanation,
        )
        for gap in gaps
    ]
    # Rank by shortfall from target (largest gap first); concept_id breaks
    # ties so the order is fully deterministic.
    items.sort(key=lambda i: (-i.gap, i.concept_id))
    return CompetencyGapResult(
        session_id=session.session_id,
        assessment_id=session.assessment_id,
        status=session.status,
        gaps=items,
    )
