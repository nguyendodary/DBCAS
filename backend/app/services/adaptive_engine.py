"""Adaptive session engine (UC12 / FR-15).

Session lifecycle
-----------------
``start_session`` creates an in-progress session (``expires_at = now +
assessment.duration_min``) and serves question 1. Resuming is
idempotent: a second call returns the learner's existing live session.

``serve_next`` returns the pending attempt as-is when one exists, so the
UI can re-request the current question safely; otherwise it picks and
persists the next Attempt plus one ``selection_log`` audit row.

``finish_session`` finalizes to ``completed`` (or ``timed_out`` once the
window has elapsed) and recomputes competency + gaps deterministically.

Adaptive policy — fully deterministic, mirroring the documented flow
-------------------------------------------------------------------
* Questions 1-3 are basic MCQs (difficulty <= 2) from the validated bank,
  spread over the assessment's target concepts.
* From question 4 the verdict of the opening phase biases difficulty
  (3 correct -> raise, 2 -> medium, 0-1 -> basic in weak concepts), and
  every subsequent pick uses the accumulated evidence: correct answers
  raise that concept's difficulty, misses probe weak or still-uncovered
  target concepts.
* The configured question mix is met through quota pressure: a sql or
  essay type is picked once ``need_type / slots_left >= 0.5`` (and always
  when slots run out). MCQs fill all other slots, so sessions reach the
  10/2/1-style targets whenever the bank can supply them.
* Only ``status='validated'`` questions with a confirmed tag to a target
  concept, inside that concept's configured difficulty range, are
  eligible — AI drafts can never be served directly (NFR-09).
* Every decision is written to ``selection_log`` (FR-15). ``is_fallback``
  marks serves where the intended type or difficulty was unavailable and
  the engine fell back so no session is blocked.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import Account, Assessment, AssessmentSession, Attempt, Question
from ..repositories import AssessmentRepository
from ..schemas import (
    EvidenceItem,
    EvidenceResult,
    McqOptionResult,
    ConceptRef,
    ServedMcqOption,
    ServedQuestion,
    ServeResult,
    SessionStateResult,
)
from . import competency_service
from .session_guard import (
    load_owned_active_session,
    load_owned_finalized_session,
)

OPENING_SIZE = 3
OPENING_MAX_DIFFICULTY = 2
QUOTA_PRESSURE_THRESHOLD = Decimal("0.5")


# ---------------------------------------------------------------- DTOs


def _served_question(repo: AssessmentRepository, attempt: Attempt) -> ServedQuestion:
    q = attempt.question
    concepts = [t.concept.concept_name for t in q.concept_tags if t.concept]
    options = [
        ServedMcqOption(
            option_id=o.option_id,
            option_label=o.option_label,
            option_text=o.option_text,
        )
        for o in q.options
    ] if q.question_type == "mcq" else []
    schema_sql = None
    if q.question_type == "sql":
        dataset = next(
            (d for d in repo.get_datasets_for_question(q.question_id)
             if not d.is_edge_case),
            None,
        )
        schema_sql = dataset.setup_sql if dataset else None
    return ServedQuestion(
        attempt_id=attempt.attempt_id,
        seq_no=attempt.seq_no,
        question_id=q.question_id,
        question_type=q.question_type,
        prompt=q.prompt,
        difficulty_level=q.difficulty_level,
        points=q.points,
        concepts=concepts,
        options=options,
        schema_sql=schema_sql,
        submitted_at=attempt.submitted_at,
        selected_option_id=attempt.selected_option_id,
        sql_answer=attempt.sql_answer,
        essay_answer=attempt.essay_answer,
        score=attempt.score,
    )


def _state(
    repo: AssessmentRepository,
    session: AssessmentSession,
    assessment: Assessment,
) -> SessionStateResult:
    attempts = repo.session_attempts(session.session_id)
    pending = next((a for a in attempts if a.submitted_at is None), None)
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    started_at = session.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    finalized = session.status != "in_progress"
    return SessionStateResult(
        session_id=session.session_id,
        assessment_id=session.assessment_id,
        assessment_title=assessment.title,
        status=session.status,
        started_at=started_at,
        expires_at=expires_at,
        submitted_at=session.submitted_at,
        remaining_seconds=max(0, int((expires_at - now).total_seconds())),
        max_questions=assessment.max_questions,
        served_count=len(attempts),
        answered_count=sum(1 for a in attempts if a.submitted_at is not None),
        current_question=_served_question(repo, pending) if pending else None,
        done=finalized or len(attempts) >= assessment.max_questions,
    )


# ------------------------------------------------------- eligibility


def _eligible_pool(
    assessment: Assessment, served_ids: set[int], repo: AssessmentRepository
) -> list[tuple[Question, list[int]]]:
    """(question, qualifying target concept_ids) for every unserved
    validated question inside at least one target concept's range."""
    ranges = {
        t.concept_id: (t.min_difficulty, t.max_difficulty)
        for t in assessment.targets
    }
    pool: list[tuple[Question, list[int]]] = []
    for q in repo.eligible_questions(assessment, served_ids):
        fits = [
            tag.concept_id
            for tag in q.concept_tags
            if tag.confirmed
            and tag.concept_id in ranges
            and ranges[tag.concept_id][0] <= q.difficulty_level <= ranges[tag.concept_id][1]
        ]
        if fits:
            pool.append((q, fits))
    return pool


# ---------------------------------------------------- evidence state


def _concept_perf(
    attempts: list[Attempt], target_ids: set[int]
) -> dict[int, dict]:
    """Per target concept: earned/possible points, last outcome, last
    difficulty — only from graded attempts (served-not-answered is not
    evidence, same rule as the competency engine)."""
    perf: dict[int, dict] = {
        cid: {"earned": Decimal("0"), "possible": Decimal("0"),
              "answered": 0, "last_correct": None, "last_diff": None}
        for cid in target_ids
    }
    for att in attempts:
        if att.submitted_at is None or att.question is None:
            continue
        q = att.question
        correct = att.score is not None and att.score >= q.points
        for tag in q.concept_tags:
            if not tag.confirmed or tag.concept_id not in perf:
                continue
            p = perf[tag.concept_id]
            p["earned"] += att.score or Decimal("0")
            p["possible"] += q.points
            p["answered"] += 1
            p["last_correct"] = correct
            p["last_diff"] = q.difficulty_level
    return perf


def _weakest_concept(candidates: list[int], perf: dict[int, dict]) -> int:
    """Lowest demonstrated competency first; uncovered concepts and ties
    resolve deterministically on concept_id."""
    def key(cid: int):
        p = perf[cid]
        pct = (p["earned"] / p["possible"]) if p["possible"] else Decimal("0")
        return (p["answered"] > 0, pct, cid)
    return min(candidates, key=key)


# ------------------------------------------------------- the pick


def _pick(
    assessment: Assessment,
    attempts: list[Attempt],
    pool: list[tuple[Question, list[int]]],
) -> tuple[Optional[Question], dict]:
    """Choose the next question; returns (question, decision_detail)."""
    served = len(attempts)
    seq_no = served + 1
    ranges = {
        t.concept_id: (t.min_difficulty, t.max_difficulty)
        for t in assessment.targets
    }
    perf = _concept_perf(attempts, set(ranges))
    by_type: dict[str, list[tuple[Question, list[int]]]] = {}
    for q, fits in pool:
        by_type.setdefault(q.question_type, []).append((q, fits))

    counts = {"mcq": 0, "sql": 0, "essay": 0}
    for a in attempts:
        if a.question is not None:
            counts[a.question.question_type] = counts.get(
                a.question.question_type, 0) + 1
    need = {
        "mcq": max(0, assessment.target_mcq - counts["mcq"]),
        "sql": max(0, assessment.target_sql - counts["sql"]),
        "essay": max(0, assessment.target_essay - counts["essay"]),
    }
    slots_left = assessment.max_questions - served
    detail: dict = {
        "phase": "opening" if served < OPENING_SIZE else "adaptive",
        "need": need,
        "slots_left": slots_left,
    }

    # ----- phase 1: opening three basic MCQs -----
    if served < OPENING_SIZE:
        wanted = "mcq"
        cands = [(q, fits) for q, fits in by_type.get("mcq", [])
                 if q.difficulty_level <= OPENING_MAX_DIFFICULTY]
        if not cands:
            cands = list(by_type.get("mcq", []))
            detail["relaxed"] = "opening_difficulty_range"
        detail["wanted_type"] = wanted
        if not cands:
            return _fallback_pick(by_type, need, detail, seq_no)
        # spread coverage: prefer a target concept not yet seen this session
        seen = {
            tag.concept_id
            for a in attempts if a.question
            for tag in a.question.concept_tags
        }
        uncovered = [(q, f) for q, f in cands
                     if any(cid not in seen for cid in f)]
        chosen_from = uncovered or cands
        q = min(chosen_from, key=lambda qf: (qf[0].difficulty_level, qf[0].question_id))[0]
        detail["served_type"] = q.question_type
        detail["reason"] = "opening_basic_mcq"
        detail["concept_ids"] = [t.concept_id for t in q.concept_tags if t.confirmed]
        return q, detail

    # ----- opening verdict bias (applies to the Q4 pick) -----
    opening_bias: Optional[int] = None
    weak_probe = False
    if served == OPENING_SIZE:
        graded = [a for a in attempts if a.submitted_at is not None]
        opening_correct = sum(
            1 for a in graded
            if a.score is not None and a.score >= a.question.points
        )
        detail["opening_correct"] = opening_correct
        if opening_correct >= OPENING_SIZE:
            opening_bias = 3
        elif opening_correct == OPENING_SIZE - 1:
            opening_bias = 2
        else:
            opening_bias = 1
            weak_probe = True
        detail["opening_bias"] = opening_bias

    # ----- type selection: quota pressure -----
    quota = sorted(
        (t for t in ("sql", "essay") if need[t] > 0),
        key=lambda t: (-need[t] / slots_left, t),
    )
    pressured = [
        t for t in quota
        if Decimal(need[t]) / Decimal(slots_left) >= QUOTA_PRESSURE_THRESHOLD
    ]
    wanted = pressured[0] if pressured else "mcq"
    detail["wanted_type"] = wanted
    detail["pressure"] = {
        t: float(Decimal(need[t]) / Decimal(slots_left)) for t in quota
    }

    cands = by_type.get(wanted, [])
    if not cands:
        for t in quota + ["mcq", "sql", "essay"]:
            if by_type.get(t):
                detail["relaxed"] = f"{wanted}_unavailable"
                cands = by_type[t]
                break
    if not cands:
        return None, detail

    # ----- concept selection: coverage first, then weakest -----
    cand_concepts = sorted({cid for _, fits in cands for cid in fits})
    uncovered = [c for c in cand_concepts if perf[c]["answered"] == 0]
    if weak_probe or uncovered:
        concept = min(uncovered or cand_concepts)
        if not uncovered:
            concept = _weakest_concept(cand_concepts, perf)
        detail["concept_reason"] = (
            "uncovered" if uncovered else "weakest"
        )
    else:
        concept = _weakest_concept(cand_concepts, perf)
        detail["concept_reason"] = "weakest"
    detail["concept_id"] = concept

    # ----- difficulty preference -----
    p = perf[concept]
    min_d, max_d = ranges[concept]
    if opening_bias is not None:
        preferred = min(max(opening_bias, min_d), max_d)
    elif p["answered"] == 0 or p["last_diff"] is None:
        preferred = min_d
    elif p["last_correct"]:
        preferred = min(p["last_diff"] + 1, max_d)
    else:
        preferred = max(p["last_diff"] - 1, min_d)
    detail["preferred_difficulty"] = preferred

    typed = [(q, fits) for q, fits in cands if concept in fits]
    q = min(
        typed,
        key=lambda qf: (
            abs(qf[0].difficulty_level - preferred),
            qf[0].difficulty_level,
            qf[0].question_id,
        ),
    )[0]
    detail["served_type"] = q.question_type
    detail["served_difficulty"] = q.difficulty_level
    return q, detail


def _fallback_pick(by_type, need, detail, seq_no):
    """Opening phase with no MCQs: serve any eligible question so the
    session is never blocked by bank composition."""
    for t in ("mcq", "sql", "essay"):
        if by_type.get(t):
            q = min(by_type[t], key=lambda qf: (qf[0].difficulty_level, qf[0].question_id))[0]
            detail["served_type"] = q.question_type
            detail["reason"] = "opening_fallback_no_mcq"
            return q, detail
    return None, detail


# ------------------------------------------------------------- API


def start_session(
    db: Session, assessment_id: int, learner: Account
) -> SessionStateResult:
    """Create (or resume) the learner's session and serve question 1."""
    repo = AssessmentRepository(db)
    assessment = repo.get_assessment(assessment_id)
    if assessment is None:
        raise AppError(404, "assessment_not_found", "Assessment not found")
    if assessment.status != "active":
        raise AppError(
            409, "assessment_not_active", "This assessment is not open"
        )

    session = repo.active_session_for(learner.account_id, assessment_id)
    if session is not None:
        # resume — flip to timed_out first if the window has elapsed
        _maybe_timeout(session, db)
        return _state(repo, session, assessment)

    expires = datetime.now(timezone.utc) + timedelta(
        minutes=assessment.duration_min
    )
    session = repo.create_session(assessment_id, learner.account_id, expires)

    question, detail = _pick(assessment, [], _eligible_pool(assessment, set(), repo))
    if question is None:
        db.rollback()
        raise AppError(
            409,
            "no_questions_available",
            "This assessment has no servable validated questions",
        )
    _serve(repo, session, question, 1, detail)
    db.commit()
    return _state(repo, session, assessment)


def serve_next(
    db: Session, session_id: int, learner: Account
) -> ServeResult:
    """Return the pending question, or adaptively serve the next one."""
    repo = AssessmentRepository(db)
    session = load_owned_active_session(repo, session_id, learner)
    assessment = repo.get_assessment(session.assessment_id)

    attempts = repo.session_attempts(session_id)
    pending = next((a for a in attempts if a.submitted_at is None), None)
    if pending is not None:
        return ServeResult(done=False, question=_served_question(repo, pending))

    if len(attempts) >= assessment.max_questions:
        return ServeResult(done=True, question=None)

    served_ids = {a.question_id for a in attempts}
    pool = _eligible_pool(assessment, served_ids, repo)
    question, detail = _pick(assessment, attempts, pool)
    if question is None:
        return ServeResult(done=True, question=None)

    attempt = _serve(repo, session, question, len(attempts) + 1, detail)
    db.commit()
    return ServeResult(done=False, question=_served_question(repo, attempt))


def _serve(
    repo: AssessmentRepository,
    session: AssessmentSession,
    question: Question,
    seq_no: int,
    detail: dict,
) -> Attempt:
    detail["served_type"] = detail.get("served_type") or question.question_type
    attempt = repo.create_attempt(
        session.session_id, question.question_id, seq_no
    )
    repo.create_selection_log(
        session.session_id,
        seq_no,
        question.question_id,
        is_fallback=detail.get("served_type") != detail.get("wanted_type")
        or "relaxed" in detail,
        decision_detail=detail,
    )
    attempt.question = question
    return attempt


def get_state(
    db: Session, session_id: int, learner: Account
) -> SessionStateResult:
    """Current session state — flips an elapsed session to timed_out."""
    repo = AssessmentRepository(db)
    session = repo.get_session(session_id)
    if session is None or session.learner_id != learner.account_id:
        raise AppError(404, "session_not_found", "Assessment session not found")
    _maybe_timeout(session, db)
    assessment = repo.get_assessment(session.assessment_id)
    return _state(repo, session, assessment)


def finish_session(
    db: Session, session_id: int, learner: Account
) -> SessionStateResult:
    """Learner submits the session (or it elapsed) -> finalize + recompute.

    Pending (served-not-answered) attempts stay unanswered and contribute
    no evidence — same rule as the competency engine.
    """
    repo = AssessmentRepository(db)
    session = repo.get_session(session_id)
    if session is None or session.learner_id != learner.account_id:
        raise AppError(404, "session_not_found", "Assessment session not found")
    if session.status == "in_progress":
        session.status = (
            "timed_out" if _expired(session) else "completed"
        )
        session.submitted_at = datetime.now(timezone.utc)
        db.commit()
    assessment = repo.get_assessment(session.assessment_id)
    # deterministic recompute: competency rows + gap sync
    competency_service.detect_session_gaps(db, session)
    return _state(repo, session, assessment)


def _expired(session: AssessmentSession) -> bool:
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= datetime.now(timezone.utc)


def _maybe_timeout(session: AssessmentSession, db: Session) -> None:
    if session.status == "in_progress" and _expired(session):
        session.status = "timed_out"
        db.commit()


def get_evidence(
    db: Session, session_id: int, learner: Account
) -> EvidenceResult:
    """UC18 — per-question evidence records, finalized sessions only."""
    repo = AssessmentRepository(db)
    session = load_owned_finalized_session(repo, session_id, learner)
    attempts = repo.session_attempts(session.session_id)
    items = [
        EvidenceItem(
            seq_no=a.seq_no,
            attempt_id=a.attempt_id,
            question_id=a.question_id,
            question_type=a.question.question_type,
            prompt=a.question.prompt,
            difficulty_level=a.question.difficulty_level,
            points=a.question.points,
            concepts=[
                ConceptRef(
                    concept_id=t.concept.concept_id,
                    concept_code=t.concept.concept_code,
                    concept_name=t.concept.concept_name,
                )
                for t in a.question.concept_tags if t.concept
            ],
            options=[
                McqOptionResult(
                    option_id=o.option_id,
                    option_label=o.option_label,
                    option_text=o.option_text,
                    is_correct=o.is_correct,
                )
                for o in a.question.options
            ] if a.question.question_type == "mcq" else [],
            selected_option_id=a.selected_option_id,
            sql_answer=a.sql_answer,
            essay_answer=a.essay_answer,
            score=a.score,
            grading_detail=a.grading_detail,
            served_at=a.served_at,
            submitted_at=a.submitted_at,
        )
        for a in attempts
    ]
    return EvidenceResult(
        session_id=session.session_id, status=session.status, items=items
    )
