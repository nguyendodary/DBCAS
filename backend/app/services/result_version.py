"""V1 official result versions for FIXED TEST sessions (PR 3B-2).

The AI score produced at finalization is the first (and, for now, only)
official result. Evidence is written to the immutable 026 tables and the
mutable publication is OFFICIAL immediately, so the learner sees the score
without a human publication step. LEGACY sessions never enter this path.
"""
import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select

from ..models import (
    Attempt,
    AttemptRubricCriterion,
    QuestionRubricCriterion,
    QuestionRubricProfile,
    SessionResultCriterionScore,
    SessionResultPublication,
    SessionResultVersion,
    SessionResultVersionScore,
)
from .evidence_context import question_view

CENT = Decimal("0.01")
ZERO = Decimal("0")


def _hash(*parts):
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_fixed_test_shape(session):
    """Server-created FIXED TEST sessions; ADAPTIVE/PRACTICE are excluded."""
    snapshot = session.config_snapshot or {}
    return (
        getattr(session, "purpose", None) == "TEST"
        and getattr(session, "purpose_source", "SERVER") == "SERVER"
        and snapshot.get("assembly_mode") != "ADAPTIVE"
        and (snapshot.get("runner_mode") == "fixed"
             or snapshot.get("assessment_style") == "FIXED")
    )


def is_ai_official(session):
    """Only server-created FIXED TEST sessions use the official AI result.

    Adaptive sessions (TEST with an ADAPTIVE assembly mode) and every
    PRACTICE session stay on the LEGACY path.
    """
    return (getattr(session, "review_policy", "LEGACY") == "AI_OFFICIAL_REVIEW"
            and is_fixed_test_shape(session))


def _decimal(value):
    return Decimal(str(value if value is not None else ZERO))


def _distribute(total: Decimal, weights: list[Decimal]) -> list[Decimal]:
    """Split ``total`` by ``weights`` so the parts sum back exactly to it."""
    if not weights:
        return []
    total = total.quantize(CENT, rounding=ROUND_HALF_UP)
    whole = sum(weights, ZERO)
    if whole <= 0:
        return [total] + [ZERO] * (len(weights) - 1)
    raw = [total * (w / whole) for w in weights]
    parts = [value.quantize(CENT, rounding=ROUND_HALF_UP) for value in raw]
    drift = (total - sum(parts, ZERO)).quantize(CENT)
    parts[-1] = (parts[-1] + drift).quantize(CENT)
    return parts


def _ensure_profile(db, session, question_id, profile_hash):
    profile = db.scalar(
        select(QuestionRubricProfile).where(
            QuestionRubricProfile.question_id == question_id,
            QuestionRubricProfile.profile_hash == profile_hash,
        )
    )
    if profile is None:
        last_version = db.scalar(
            select(func.max(QuestionRubricProfile.version_no)).where(
                QuestionRubricProfile.question_id == question_id)
        ) or 0
        profile = QuestionRubricProfile(
            question_id=question_id,
            version_no=last_version + 1,
            status="active",
            profile_hash=profile_hash,
            created_by=session.learner_id,
        )
        db.add(profile)
        db.flush()
    return profile


def _ensure_criterion(db, profile, max_score):
    code = f"AI_V1_{int(max_score * 100)}"
    criterion = db.scalar(
        select(QuestionRubricCriterion).where(
            QuestionRubricCriterion.rubric_profile_id == profile.rubric_profile_id,
            QuestionRubricCriterion.criterion_code == code,
        )
    )
    if criterion is None:
        last_order = db.scalar(
            select(func.max(QuestionRubricCriterion.sort_order)).where(
                QuestionRubricCriterion.rubric_profile_id == profile.rubric_profile_id)
        ) or 0
        criterion = QuestionRubricCriterion(
            rubric_profile_id=profile.rubric_profile_id,
            criterion_code=code,
            criterion_name="AI overall score",
            description="Deterministic AI score snapshot for the official v1 result.",
            scoring_guidance="One additive criterion carrying the graded essay score.",
            max_points=max_score,
            sort_order=last_order + 1,
            criterion_hash=_hash("criterion", code, str(max_score)),
        )
        db.add(criterion)
        db.flush()
    return criterion


def _criterion_rows(db, session, version_id, attempt, score, max_score):
    """Build criterion scores for one essay attempt.

    Pre-existing rubric snapshots are reused; a single deterministic snapshot
    is created when the essay has none (the legacy four-level rubric is not an
    additive criterion profile). The 026 completeness/totals triggers require
    every snapshot to have one score whose max_points equals the snapshot's.
    """
    profile_hash = (attempt.question_snapshot or {}).get("rubric_snapshot_hash")
    arcs = list(db.scalars(
        select(AttemptRubricCriterion)
        .where(AttemptRubricCriterion.session_id == session.session_id,
               AttemptRubricCriterion.attempt_id == attempt.attempt_id)
        .order_by(AttemptRubricCriterion.sort_order,
                  AttemptRubricCriterion.criterion_snapshot_id)
    ))
    if not arcs:
        profile = _ensure_profile(db, session, attempt.question_id, profile_hash)
        criterion = _ensure_criterion(db, profile, max_score)
        arc = AttemptRubricCriterion(
            session_id=session.session_id,
            attempt_id=attempt.attempt_id,
            question_id=attempt.question_id,
            rubric_profile_id=profile.rubric_profile_id,
            criterion_id=criterion.criterion_id,
            criterion_code=criterion.criterion_code,
            criterion_name=criterion.criterion_name,
            description=criterion.description,
            scoring_guidance=criterion.scoring_guidance,
            max_points=criterion.max_points,
            sort_order=criterion.sort_order,
            profile_snapshot_hash=profile.profile_hash,
            criterion_hash=criterion.criterion_hash,
        )
        db.add(arc)
        db.flush()
        arcs = [arc]
    weights = [a.max_points for a in arcs]
    parts = _distribute(score, weights)
    return [
        SessionResultCriterionScore(
            session_id=session.session_id,
            result_version_id=version_id,
            attempt_id=attempt.attempt_id,
            criterion_snapshot_id=arc.criterion_snapshot_id,
            score=part,
            max_points=arc.max_points,
        )
        for arc, part in zip(arcs, parts)
    ]


def ensure_official_v1(db, session):
    """Idempotently publish the graded attempt scores as V1/OFFICIAL.

    Called from the single finalize transaction. Returns the version row, or
    ``None`` for sessions that are not on the AI-official path. A second
    finalize (or a late caller) never duplicates the version or its scores.
    """
    if not is_ai_official(session):
        return None
    if session.current_result_version_id is not None:
        return None
    existing = db.scalar(
        select(SessionResultVersion)
        .where(SessionResultVersion.session_id == session.session_id,
               SessionResultVersion.version_no == 1)
    )
    if existing is not None:
        _publish(db, session, existing.result_version_id)
        return existing

    attempts = list(db.scalars(
        select(Attempt)
        .where(Attempt.session_id == session.session_id)
        .order_by(Attempt.seq_no, Attempt.attempt_id)
    ))
    prepared, total, maximum = [], ZERO, ZERO
    for attempt in attempts:
        question = question_view(attempt)
        max_score = _decimal(question.points)
        score = min(_decimal(attempt.score), max_score).quantize(
            CENT, rounding=ROUND_HALF_UP)
        prepared.append((attempt, question, score, max_score))
        total += score
        maximum += max_score

    # 026 freezes question snapshots: an essay can only join V1 when its
    # captured rubric identity can back a complete, matching criterion set.
    for attempt, question, _, max_score in prepared:
        if question.question_type != "essay":
            continue
        profile_hash = (attempt.question_snapshot or {}).get("rubric_snapshot_hash")
        if not profile_hash:
            return None
        frozen = list(db.scalars(
            select(AttemptRubricCriterion).where(
                AttemptRubricCriterion.session_id == session.session_id,
                AttemptRubricCriterion.attempt_id == attempt.attempt_id)
        ))
        if frozen and (any(a.profile_snapshot_hash != profile_hash for a in frozen)
                       or sum((a.max_points for a in frozen), ZERO) != max_score):
            return None

    version = SessionResultVersion(
        session_id=session.session_id,
        version_no=1,
        source="V1",
        total_score=total,
        max_score=maximum,
        result_hash=_hash("v1", session.session_id,
                          [(a.attempt_id, str(s), str(m)) for a, _, s, m in prepared]),
    )
    db.add(version)
    db.flush()

    for attempt, question, score, max_score in prepared:
        db.add(SessionResultVersionScore(
            session_id=session.session_id,
            result_version_id=version.result_version_id,
            attempt_id=attempt.attempt_id,
            score=score,
            max_score=max_score,
            source="MACHINE",
        ))
        db.flush()
        if question.question_type == "essay":
            db.add_all(_criterion_rows(
                db, session, version.result_version_id, attempt, score, max_score))
            db.flush()

    _publish(db, session, version.result_version_id)
    return version


def _publish(db, session, result_version_id):
    publication = db.scalar(
        select(SessionResultPublication).where(
            SessionResultPublication.result_version_id == result_version_id)
    )
    now = db.scalar(select(func.clock_timestamp()))
    if publication is None:
        db.add(SessionResultPublication(
            result_version_id=result_version_id,
            session_id=session.session_id,
            state="OFFICIAL",
            published_at=now,
        ))
    elif publication.state != "OFFICIAL":
        publication.state = "OFFICIAL"
        publication.published_at = now
    db.flush()
    session.current_result_version_id = result_version_id
    db.flush()


def version_meta(db, session):
    """Response metadata shared by the learner result/state surfaces."""
    meta = {
        "result_version": None,
        "is_current": False,
        "review_status": ("PENDING" if getattr(session, "review_policy", "LEGACY")
                          == "AI_OFFICIAL_REVIEW" else "LEGACY"),
        "can_request_review": False,
    }
    if getattr(session, "current_result_version_id", None) is not None:
        version = db.get(SessionResultVersion, session.current_result_version_id)
        if version is not None:
            meta["result_version"] = version.version_no
        meta["is_current"] = True
        publication = db.scalar(
            select(SessionResultPublication).where(
                SessionResultPublication.result_version_id
                == session.current_result_version_id)
        )
        if publication is not None:
            meta["review_status"] = publication.state
    else:
        version = db.scalar(
            select(SessionResultVersion)
            .where(SessionResultVersion.session_id == session.session_id)
            .order_by(SessionResultVersion.version_no.desc())
        )
        if version is not None:
            meta["result_version"] = version.version_no
            meta["review_status"] = "PENDING"
    return meta


def current_scores(db, session):
    """``{attempt_id: score}`` from the session's current result version.

    Legacy sessions (and AI-official sessions without a published version)
    return an empty mapping so callers keep reading ``attempt.score``.
    """
    if not is_ai_official(session) or session.current_result_version_id is None:
        return {}
    rows = db.execute(
        select(SessionResultVersionScore.attempt_id, SessionResultVersionScore.score)
        .where(SessionResultVersionScore.session_id == session.session_id,
               SessionResultVersionScore.result_version_id
               == session.current_result_version_id)
    ).all()
    return {attempt_id: _decimal(score) for attempt_id, score in rows}
