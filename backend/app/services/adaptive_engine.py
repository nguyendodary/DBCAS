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

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import Account, Assessment, AssessmentSession, Attempt, Question, SessionQuestionPlan
from ..repositories import AssessmentRepository
from ..schemas import (
    EvidenceItem,
    EvidenceRubric,
    EvidenceResult,
    McqOptionResult,
    EvidenceMcqOption,
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

from .evidence_context import capture_assessment, capture_question, question_view, assessment_view

OPENING_SIZE = 3
OPENING_MAX_DIFFICULTY = 2
QUOTA_PRESSURE_THRESHOLD = Decimal("0.5")


# ---------------------------------------------------------------- DTOs


def _served_question(repo: AssessmentRepository, attempt: Attempt, locale="en") -> ServedQuestion:
    from .dataset_preview import dataset_tables
    q = question_view(attempt, locale)
    concepts = [t.concept.concept_name for t in q.concept_tags if t.confirmed and t.concept]
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
        datasets = q.datasets if attempt.question_snapshot else repo.get_datasets_for_question(q.question_id)
        dataset = next((d for d in datasets if not d.is_edge_case), datasets[0] if datasets else None)
        schema_sql = dataset.setup_sql if dataset else None
    return ServedQuestion(
        attempt_id=attempt.attempt_id,
        seq_no=attempt.seq_no,
        question_id=q.question_id,
        question_type=q.question_type,
        content_locale=getattr(q, "content_locale", "en"),
        prompt=q.prompt,
        difficulty_level=q.difficulty_level,
        points=q.points,
        concepts=concepts,
        options=options,
        multiple_answers=sum(bool(option.is_correct) for option in q.options) > 1 if q.question_type == "mcq" else False,
        schema_sql=schema_sql,
        data_tables=dataset_tables(schema_sql) if schema_sql else [],
        submitted_at=attempt.submitted_at,
        selected_option_id=attempt.selected_option_id,
        selected_option_ids=getattr(attempt, "selected_option_ids", None) or ([attempt.selected_option_id] if attempt.selected_option_id is not None else []),
        sql_answer=attempt.sql_answer,
        essay_answer=attempt.essay_answer,
        score=attempt.score,
        draft=attempt.draft_answer if attempt.draft_answer is not None else (
            {"selected_option_ids": attempt.selected_option_ids or ([attempt.selected_option_id] if attempt.selected_option_id is not None else [])}
            if q.question_type == "mcq" else {"sql_answer": attempt.sql_answer} if q.question_type == "sql" else {"essay_answer": attempt.essay_answer}
        ) if attempt.submitted_at is not None else attempt.draft_answer,
        draft_revision=attempt.draft_revision,
        grading_status=attempt.grading_status,
    )


def free_navigation(repo, session, attempts=None):
    if (session.config_snapshot or {}).get("navigation_mode") == "FREE":
        return True
    attempts = attempts if attempts is not None else repo.session_attempts(session.session_id)
    assessment = assessment_view(session, repo)
    return len(attempts) == assessment.max_questions and repo.db.scalar(
        select(SessionQuestionPlan.session_id).where(SessionQuestionPlan.session_id == session.session_id).limit(1)
    ) is not None


def enable_navigation(db, session_id, learner):
    """Freeze the remaining legacy questions without replacing saved evidence."""
    from collections import Counter
    from .personalized_assessment import select_questions, serve_planned
    repo = AssessmentRepository(db)
    session = load_owned_active_session(repo, session_id, learner)
    attempts = repo.session_attempts(session_id)
    if free_navigation(repo, session, attempts):
        return _state(repo, session)
    assessment = assessment_view(session, repo)
    if (session.config_snapshot or {}).get("question_plan"):
        for seq in range(len(attempts) + 1, assessment.max_questions + 1):
            serve_planned(repo, session, seq)
    else:
        counts = Counter(question_view(a).question_type for a in attempts)
        extra = assessment.max_questions - assessment.target_mcq - assessment.target_sql - assessment.target_essay
        quotas = {kind: max(0, count - counts[kind]) for kind, count in
                  (("mcq", assessment.target_mcq + extra), ("sql", assessment.target_sql), ("essay", assessment.target_essay))}
        if sum(quotas.values()) != assessment.max_questions - len(attempts):
            raise AppError(409, "question_mix_changed", "The existing session has a different question mix and cannot be expanded safely")
        chosen = select_questions(_eligible_pool(assessment, {a.question_id for a in attempts}, repo), [], quotas)
        chosen.sort(key=lambda q: ({"mcq": 0, "sql": 1, "essay": 2}[q.question_type], q.difficulty_level))
        for question in sorted(chosen, key=lambda q: q.question_id):
            db.scalar(select(Question).where(Question.question_id == question.question_id).with_for_update(read=True))
        for seq, question in enumerate(chosen, len(attempts) + 1):
            _serve(repo, session, question, seq, {"phase": "fixed_navigation", "wanted_type": question.question_type})
        db.add_all([SessionQuestionPlan(session_id=session_id, seq_no=a.seq_no, question_id=a.question_id)
                    for a in repo.session_attempts(session_id)])
    db.commit()
    return _state(repo, session)


def _state(
    repo: AssessmentRepository,
    session: AssessmentSession,
    assessment: Assessment = None,
) -> SessionStateResult:
    assessment = assessment_view(session, repo)
    attempts = repo.session_attempts(session.session_id)
    free = free_navigation(repo, session, attempts)
    def answered(a):
        return a.submitted_at is not None or any(bool(v.strip()) if isinstance(v, str) else bool(v) for v in (a.draft_answer or {}).values())
    pending = next((a for a in attempts if not answered(a)), attempts[0] if free and attempts else None)
    now = repo.server_time()
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    started_at = session.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    finalized = session.status != "in_progress"
    return SessionStateResult(
        navigation_mode="FREE" if free else "SEQUENTIAL",
        questions=[_served_question(repo, a, session.locale or "en") for a in attempts] if free and not finalized else [],
        session_id=session.session_id,
        assessment_id=session.assessment_id,
        assessment_title=assessment.title,
        locale=session.locale or "en",
        result_release_policy=session.result_release_policy,
        release_status=session.release_status,
        selected_concept_ids=(session.config_snapshot or {}).get("selected_concept_ids", []),
        difficulty=(session.config_snapshot or {}).get("difficulty"),
        assembly_mode=(session.config_snapshot or {}).get("assembly_mode"),
        status=session.status,
        started_at=started_at,
        expires_at=expires_at,
        submitted_at=session.submitted_at,
        remaining_seconds=max(0, int((expires_at - now).total_seconds())),
        server_now=now,
        max_questions=assessment.max_questions,
        served_count=len(attempts),
        answered_count=sum(1 for a in attempts if answered(a)) if free else sum(1 for a in attempts if a.submitted_at is not None),
        current_question=_served_question(repo, pending, session.locale or "en") if pending else None,
        done=finalized if free else finalized or len(attempts) >= assessment.max_questions,
    )


# ------------------------------------------------------- eligibility


def _eligible_pool(
    assessment: Assessment, served_ids: set[int], repo: AssessmentRepository, *, opening_only=False
) -> list[tuple[Question, list[int]]]:
    """(question, qualifying target concept_ids) for every unserved
    validated question inside at least one target concept's range."""
    ranges = {
        t.concept_id: (t.min_difficulty, t.max_difficulty)
        for t in assessment.targets
    }
    pool: list[tuple[Question, list[int]]] = []
    from .question_service import _validation_missing
    from ..repositories import QuestionRepository
    bank = QuestionRepository(repo.db)
    used_families = repo.question_families(served_ids)
    for q in repo.eligible_questions(assessment, served_ids, opening_only=opening_only):
        if (q.family_id or q.question_id) in used_families or _validation_missing(bank, q):
            continue
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
        if att.submitted_at is None or att.score is None:
            continue
        q = question_view(att)
        if q is None:
            continue
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
            counts[question_view(a).question_type] = counts.get(
                question_view(a).question_type, 0) + 1
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
        detail["wanted_type"] = wanted
        if not cands:
            raise AppError(422, "opening_bank_incomplete", "The mandatory three basic MCQs are unavailable. Contact the administrator.")
        # spread coverage: prefer a target concept not yet seen this session
        seen = {
            tag.concept_id
            for a in attempts if a.question
            for tag in question_view(a).concept_tags
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
            if a.score is not None and a.score >= question_view(a).points
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


# ------------------------------------------------------------- API


def start_session(
    db: Session, assessment_id: int, learner: Account, *, locale="en", selection=None
) -> SessionStateResult:
    """Create (or resume) the learner's session and serve question 1."""
    if selection is not None:
        from .personalized_assessment import start_session as start_personalized
        return start_personalized(db, assessment_id, learner, selection, locale=locale)
    repo = AssessmentRepository(db)
    from ..repositories import SecurityRepository
    SecurityRepository(db).lock(f"assessment-start:{learner.account_id}:{assessment_id}")
    assessment = repo.get_assessment(assessment_id)
    if assessment is None:
        raise AppError(404, "assessment_not_found", "Assessment not found")
    if assessment.status != "published":
        raise AppError(
            409, "assessment_not_active", "This assessment is not open"
        )

    session = repo.active_session_for(learner.account_id, assessment_id)
    if session is not None:
        # resume — flip to timed_out first if the window has elapsed
        _maybe_timeout(session, db)
        return _state(repo, session, assessment)

    from .assessment_validation import validate_assessment_bank
    validate_assessment_bank(db, assessment)
    started_at = repo.server_time()
    expires = started_at + timedelta(
        minutes=assessment.duration_min
    )
    from .question_localization import normalize_locale
    session = repo.create_session(assessment_id, learner.account_id, expires, started_at=started_at,
                                  locale=normalize_locale(locale), result_release_policy=assessment.result_release_policy)
    from .personalized_assessment import select_questions
    pool = _eligible_pool(assessment, set(), repo)
    extra = assessment.max_questions - assessment.target_mcq - assessment.target_sql - assessment.target_essay
    chosen = select_questions(pool, [], {"mcq": assessment.target_mcq + extra,
                                        "sql": assessment.target_sql, "essay": assessment.target_essay})
    # Lock in a stable order, then freeze every item before a learner starts.
    for question in sorted(chosen, key=lambda q: q.question_id):
        db.scalar(select(Question).where(Question.question_id == question.question_id).with_for_update(read=True))
    eligible_ids = {q.question_id for q, _ in _eligible_pool(assessment, set(), repo)}
    if any(q.question_id not in eligible_ids for q in chosen):
        raise AppError(409, "question_bank_changed", "The question bank changed. Please retry.")
    chosen.sort(key=lambda q: ({"mcq": 0, "sql": 1, "essay": 2}[q.question_type], q.difficulty_level))
    session.config_snapshot = {**capture_assessment(assessment), "navigation_mode": "FREE"}
    for seq, question in enumerate(chosen, 1):
        _serve(repo, session, question, seq, {"phase": "fixed", "wanted_type": question.question_type})
    db.commit()
    return _state(repo, session, assessment)


def serve_next(
    db: Session, session_id: int, learner: Account, *, commit=True
) -> ServeResult:
    """Return the pending question, or adaptively serve the next one."""
    repo = AssessmentRepository(db)
    session = load_owned_active_session(repo, session_id, learner)
    assessment = assessment_view(session, repo)

    attempts = repo.session_attempts(session_id)
    pending = next((a for a in attempts if a.submitted_at is None), None)
    if pending is not None:
        return ServeResult(done=False, question=_served_question(repo, pending, session.locale or "en"))

    if len(attempts) >= assessment.max_questions:
        return ServeResult(done=True, question=None)

    if (session.config_snapshot or {}).get("personalized"):
        from .personalized_assessment import serve_planned
        attempt = serve_planned(repo, session, len(attempts) + 1)
        if commit:
            db.commit()
        return ServeResult(done=False, question=_served_question(repo, attempt, session.locale or "en"))

    served_ids = {a.question_id for a in attempts}
    pool = _eligible_pool(assessment, served_ids, repo, opening_only=len(attempts) < OPENING_SIZE)
    question, detail = _pick(assessment, attempts, pool)
    if question is None:
        return ServeResult(done=True, question=None)

    attempt = _serve(repo, session, question, len(attempts) + 1, detail)
    if commit:
        db.commit()
    return ServeResult(done=False, question=_served_question(repo, attempt, session.locale or "en"))


def _serve(
    repo: AssessmentRepository,
    session: AssessmentSession,
    question: Question,
    seq_no: int,
    detail: dict,
) -> Attempt:
    question = repo.lock_question_for_serving(question.question_id)
    if question is None or question.status != "validated":
        raise AppError(409, "question_bank_changed", "The question bank changed. Retry to load the current assessment question.")
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
    attempt.question_snapshot = capture_question(repo, question)
    return attempt


def get_state(
    db: Session, session_id: int, learner: Account
) -> SessionStateResult:
    """Current session state — flips an elapsed session to timed_out."""
    repo = AssessmentRepository(db)
    session = repo.lock_session(session_id)
    if session is None or session.learner_id != learner.account_id:
        raise AppError(404, "session_not_found", "Assessment session not found")
    _maybe_timeout(session, db)
    return _state(repo, session)


def finish_session(
    db: Session, session_id: int, learner: Account, *, result_release_policy=None
) -> SessionStateResult:
    """Learner submits the session (or it elapsed) -> finalize + recompute.

    Pending (served-not-answered) attempts stay unanswered and contribute
    no evidence — same rule as the competency engine.
    """
    repo = AssessmentRepository(db)
    session = repo.lock_session(session_id)
    if session is None or session.learner_id != learner.account_id:
        raise AppError(404, "session_not_found", "Assessment session not found")
    if result_release_policy is not None:
        if result_release_policy not in {"IMMEDIATE", "HUMAN_VERIFIED"}:
            raise AppError(422, "invalid_release_policy", "Invalid result release choice")
        if session.status == "in_progress" and session.release_policy_chosen_at is None:
            session.result_release_policy = result_release_policy
            session.release_policy_chosen_at = repo.server_time()
            db.flush()  # Persist the choice before finalization/reconciliation.
        elif session.result_release_policy != result_release_policy:
            raise AppError(409, "release_choice_locked", "The submitted result release choice cannot be changed")
    from .assessment_lifecycle import finalize
    finalize(db, session)
    return _state(repo, session)


def _expired(session: AssessmentSession, now: datetime) -> bool:
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= now


def _maybe_timeout(session: AssessmentSession, db: Session) -> None:
    if session.status == "in_progress" and _expired(session, AssessmentRepository(db).server_time()):
        from .assessment_lifecycle import finalize
        finalize(db, session, timed_out=True)


def get_evidence(
    db: Session, session_id: int, learner: Account
) -> EvidenceResult:
    """UC18 — per-question evidence records, finalized sessions only."""
    repo = AssessmentRepository(db)
    session = load_owned_finalized_session(repo, session_id, learner)
    attempts = repo.session_attempts(session.session_id)
    items = []
    for a in attempts:
        q = question_view(a, session.locale or "en")
        feedback_ready = session.result_release_policy == "HUMAN_VERIFIED" or bool(a.review_revision)
        grading_detail = dict(a.grading_detail) if a.grading_detail else None
        content_locale = getattr(q, "content_locale", "en")
        if grading_detail and content_locale != "en":
            localized_rubrics = (a.question_snapshot or {}).get("localized_content", {}).get(content_locale, {}).get("rubrics", {})
            level = grading_detail.get("rubric_level")
            if level in localized_rubrics:
                grading_detail["rubric_level_label"] = localized_rubrics[level].get("label", level)
        items.append(EvidenceItem(
            feedback_pending=not feedback_ready,
            reference_answer=q.reference_answer if feedback_ready else None,
            seq_no=a.seq_no,
            attempt_id=a.attempt_id,
            question_id=a.question_id,
            question_type=q.question_type,
            content_locale=content_locale,
            prompt=q.prompt,
            explanation=q.explanation if feedback_ready else None,
            difficulty_level=q.difficulty_level,
            points=q.points,
            concepts=[
                ConceptRef(
                    concept_id=t.concept.concept_id,
                    concept_code=t.concept.concept_code,
                    concept_name=t.concept.concept_name,
                )
                for t in q.concept_tags if t.concept
            ],
            options=[
                EvidenceMcqOption(
                    option_id=o.option_id,
                    option_label=o.option_label,
                    option_text=o.option_text,
                    is_correct=o.is_correct if feedback_ready else None,
                )
                for o in q.options
            ] if q.question_type == "mcq" else [],
            rubrics=[EvidenceRubric(
                level_name=r.level_name,
                display_label=getattr(r, "display_label", r.level_name),
                min_score=r.min_score,
                max_score=r.max_score,
                criteria=r.criteria,
            ) for r in q.rubrics] if q.question_type == "essay" and feedback_ready else [],
            selected_option_id=a.selected_option_id,
            selected_option_ids=getattr(a, "selected_option_ids", None) or ([a.selected_option_id] if a.selected_option_id is not None else []),
            sql_answer=a.sql_answer,
            essay_answer=a.essay_answer,
            score=a.score,
            grading_detail=grading_detail if feedback_ready else None,
            served_at=a.served_at,
            submitted_at=a.submitted_at,
        ))
    return EvidenceResult(
        session_id=session.session_id, status=session.status, items=items
    )
