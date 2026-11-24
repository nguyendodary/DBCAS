"""Mode 2: live AI questions inside an adaptive practice session.

The generated question is validated before it is served; a provider timeout,
rejection or disabled key always falls back to the reviewed bank.  The next
question is prefetched for both possible difficulty outcomes while the learner
is answering the current one, so a normal transition does not wait on a
provider call.
"""
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
import logging
import threading
import time
from types import SimpleNamespace

from sqlalchemy import select

from ..config import get_settings
from ..errors import AppError
from ..models import (
    Concept,
    Question,
    QuestionConcept,
    SessionQuestionPlan,
    SessionStartRequest,
)
from ..repositories import AssessmentRepository, QuestionRepository
from .blueprints import DIFFICULTY_BANDS
from .evidence_context import capture_question
from .llm.provider import ChatMessage
from .practice_generation import GeneratedQuestion, levels, validate_generated
from .practice_service import PracticeMix

LOG = logging.getLogger("dbcas.ai.practice")
POLICY = {
    "version": "ai-adaptive-v1",
    "question_types": ["mcq", "sql", "essay"],
    "correct_ratio": 0.5,
}
LEVELS = ("mcq", "sql", "essay")
_PREFETCH = {}
_PREFETCH_LOCK = threading.Lock()
_PREFETCH_MAX = 200


def _band_bounds(band):
    return DIFFICULTY_BANDS[band]


def _start_level(band):
    return _band_bounds(band)[0]


def _clamp_level(level, band):
    low, high = _band_bounds(band)
    return min(high, max(low, int(level)))


def _next_level(level, correct, band):
    delta = 1 if correct else -1
    return _clamp_level(level + delta, band)


def _correct(attempt):
    snapshot = attempt.question_snapshot or {}
    if snapshot.get("question_type") == "mcq":
        correct_id = next(
            (option["option_id"] for option in snapshot.get("options", []) if option.get("is_correct")),
            None,
        )
        return attempt.selected_option_id is not None and attempt.selected_option_id == correct_id
    score = attempt.score
    points = snapshot.get("points")
    if score is None or points is None:
        return False
    return float(score) >= float(points) * POLICY["correct_ratio"]


def _mix(payload):
    if payload.question_mix is not None:
        return payload.question_mix
    return PracticeMix(mcq=payload.question_count)


def _type_sequence(payload):
    mix = _mix(payload)
    counts = {kind: getattr(mix, kind) for kind in LEVELS if getattr(mix, kind)}
    sequence = []
    while len(sequence) < payload.question_count:
        before = len(sequence)
        for kind in LEVELS:
            if counts.get(kind, 0) > sequence.count(kind):
                sequence.append(kind)
                if len(sequence) >= payload.question_count:
                    break
        if len(sequence) == before:
            break
    if len(sequence) != payload.question_count:
        raise AppError(422, "invalid_question_mix", "The question mix does not match the question count")
    return sequence


def _level_for(seq, attempts, adaptive):
    if not attempts:
        return _clamp_level(adaptive["start_level"], adaptive["start_band"])
    last = attempts[-1]
    level = int((last.question_snapshot or {}).get("difficulty_level") or adaptive["start_level"])
    return _next_level(level, _correct(last), adaptive["start_band"])


def _cache_key(session_id, seq, kind, level):
    return (int(session_id), int(seq), str(kind), int(level))


def _take_prefetch(session_id, seq, kind, level):
    with _PREFETCH_LOCK:
        return _PREFETCH.pop(_cache_key(session_id, seq, kind, level), None)


def _store_prefetch(session_id, seq, kind, level, item):
    with _PREFETCH_LOCK:
        if len(_PREFETCH) >= _PREFETCH_MAX:
            _PREFETCH.pop(next(iter(_PREFETCH)))
        _PREFETCH[_cache_key(session_id, seq, kind, level)] = item


def _prompt(concept, kind, level, band, locale):
    language = "Vietnamese" if locale == "vi" else "English"
    extra = {
        "mcq": "Return exactly four options, exactly one correct; reference_answer must equal the correct option text.",
        "sql": "Provide a runnable PostgreSQL reference_answer and both setup_sql and edge_setup_sql. The reference answer may use SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER or DROP inside the sandbox; it must be deterministic.",
        "essay": "Provide a reference_answer and four continuous rubrics Incomplete, Partial, Mostly Complete, Complete covering the full points range.",
    }[kind]
    return (
        f"Create exactly one {kind} PostgreSQL practice question in {language}. "
        f"Concept: {concept.concept_name} ({concept.concept_code}). "
        f"Difficulty level: {level} (band {band}, allowed {levels(SimpleNamespace(difficulties=[band]))}). "
        f"Return one JSON object with concept_ids [{concept.concept_id}], question_type {kind}, "
        f"difficulty_level {level}, a non-empty explanation, source_refs, reference_answer and points. "
        f"{extra} Do not use the current time, random values, catalogs or side effects outside the provided dataset. "
        "The object must match the supplied JSON schema exactly."
    )


def _generate_one(db, concept, kind, level, band, locale, llm, runner, session_id,
                  seq_no, timeout_seconds, request_id):
    if llm is None or not getattr(llm, "is_configured", lambda: False)():
        raise RuntimeError("llm_not_configured")
    deadline = time.monotonic() + timeout_seconds
    call_llm = llm.with_budget(timeout_seconds=timeout_seconds, max_retries=0) if hasattr(llm, "with_budget") else llm
    schema = GeneratedQuestion.model_json_schema()
    prompt = _prompt(concept, kind, level, band, locale)
    raw = call_llm.generate_structured(
        "ai_practice",
        [ChatMessage("user", prompt)],
        json_schema={"name": "ai_practice_question", "strict": True, "schema": schema},
        max_tokens=5000,
        context_version=f"ai-practice:{session_id}:{seq_no}:{request_id}",
        validator=lambda value: value,
    )
    if not isinstance(raw, dict):
        raise ValueError("generation_schema")
    if isinstance(raw.get("question"), dict):
        raw = raw["question"]
    if "questions" not in raw:
        raw = {"questions": [raw]}
    proxy = SimpleNamespace(
        question_count=1,
        difficulties=[band],
        concept_ids=[concept.concept_id],
        source="ai",
    )
    validated = validate_generated(
        raw,
        [concept],
        proxy,
        runner,
        deadline=deadline,
        allowed_types={kind},
        expected_types={kind: 1},
        original_locale=locale,
    )
    if not validated:
        raise ValueError("generation_empty")
    item = validated[0]
    item["_origin"] = "ai"
    item["_generation"] = {
        "version": "practice-ai-v1",
        "request_id": str(request_id),
        "session_id": int(session_id),
        "seq_no": int(seq_no),
        "difficulty": band,
        "level": int(level),
        "locale": locale,
        "model": getattr(getattr(llm, "_settings", None), "llm_model", "injected-provider"),
    }
    return item


def _fallback_bank(db, concept_id, kind, level, band, used):
    low, high = _band_bounds(band)
    repo = QuestionRepository(db)
    base = (
        select(Question)
        .join(QuestionConcept, QuestionConcept.question_id == Question.question_id)
        .where(
            Question.status == "validated",
            Question.source == "bank",
            Question.question_type == kind,
            QuestionConcept.concept_id == concept_id,
            QuestionConcept.confirmed.is_(True),
            Question.question_id.not_in(used or {0}),
        )
    )
    rows = list(db.scalars(base))
    if not rows:
        return None
    exact = [row for row in rows if low <= row.difficulty_level <= high]

    def distance(row):
        candidate = row.difficulty_level if exact else row.difficulty_level
        return abs(candidate - level), row.question_id

    row = min(exact or rows, key=distance)
    loaded = repo.get_detail(row.question_id)
    if loaded is None:
        return None
    return {"question": loaded, "origin": "bank", "fallback_reason": "ai_unavailable"}


def _staging_question(db, item, concept, learner_id, locale):
    repo = QuestionRepository(db)
    question = Question(
        question_type=item["question_type"],
        prompt=item["prompt"],
        reference_answer=item.get("reference_answer"),
        difficulty_level=int(item["difficulty_level"]),
        source="ai_generated",
        status="retired",
        points=item.get("points", 1),
        created_by=learner_id,
        original_locale=item.get("original_locale", locale),
        explanation=item.get("explanation"),
        source_refs=[{"url": url} for url in item.get("source_refs", [])],
        ai_review={"generation": item.get("_generation")},
    )
    db.add(question)
    db.flush()
    repo.replace_options(question, [
        SimpleNamespace(option_label=str(option.get("option_label") or chr(65 + index)),
                        option_text=str(option.get("option_text", option.get("text", "")) or ""),
                        is_correct=bool(option.get("is_correct", option.get("correct", False))))
        for index, option in enumerate(item.get("options") or [])
    ])
    repo.replace_datasets(question, [
        SimpleNamespace(dataset_name=str(dataset.get("dataset_name") or "dataset"),
                        setup_sql=str(dataset.get("setup_sql") or ""),
                        expected_result=dataset.get("expected_result") or {"rows": []},
                        is_edge_case=bool(dataset.get("is_edge_case")))
        for dataset in item.get("_datasets") or []
    ])
    repo.replace_rubrics(question, [
        SimpleNamespace(level_name=str(rubric.get("level_name") or ""),
                        min_score=rubric.get("min_score"),
                        max_score=rubric.get("max_score"),
                        criteria=str(rubric.get("criteria") or ""))
        for rubric in item.get("rubrics") or []
    ])
    repo.upsert_tag(question.question_id, concept.concept_id, source="ai",
                    confirmed=True, is_required=True)
    db.flush()
    db.refresh(question)
    snapshot = capture_question(AssessmentRepository(db), question)
    snapshot["source"] = "ai_generated"
    snapshot["origin"] = "ai"
    snapshot["generation"] = item.get("_generation")
    return question, snapshot


def _persist(repo, session, attempt_question, snapshot, seq_no, decision):
    repo.db.add(SessionQuestionPlan(session_id=session.session_id, seq_no=seq_no,
                                    question_id=attempt_question.question_id))
    attempt = repo.create_attempt(session.session_id, attempt_question.question_id, seq_no)
    attempt.question_snapshot = snapshot
    repo.create_selection_log(session.session_id, seq_no, attempt_question.question_id,
                              is_fallback=decision["is_fallback"], decision_detail=decision)
    return attempt


def _serve(repo, session, attempts, llm, runner, *, seq_no=None):
    snapshot = session.config_snapshot or {}
    adaptive = snapshot.get("adaptive") or {}
    if adaptive.get("policy_version") != POLICY["version"]:
        raise AppError(409, "adaptive_policy_unavailable", "The saved adaptive policy is unavailable")
    seq = int(seq_no or (len(attempts) + 1))
    target = int(snapshot.get("max_questions") or 0)
    if seq > target:
        return None
    sequence = adaptive.get("type_sequence") or []
    kind = sequence[seq - 1] if seq - 1 < len(sequence) else "mcq"
    level = _level_for(seq, attempts, adaptive)
    used = {attempt.question_id for attempt in attempts}
    concept = repo.db.get(Concept, adaptive["concept_id"])
    if concept is None:
        raise AppError(404, "concept_not_found", "Concept not found")
    item = _take_prefetch(session.session_id, seq, kind, level)
    fallback_reason = None
    if item is None:
        try:
            item = _generate_one(
                repo.db, concept, kind, level, adaptive["start_band"],
                session.locale or "vi", llm, runner, session.session_id, seq,
                adaptive.get("timeout_seconds", 10), adaptive.get("seed"),
            )
        except Exception as exc:  # provider, timeout, schema or content rejection
            fallback_reason = getattr(exc, "code", None) or type(exc).__name__
            LOG.info("AI practice fallback session=%s seq=%s type=%s level=%s reason=%s detail=%s",
                     session.session_id, seq, kind, level, fallback_reason,
                     getattr(exc, "excerpt", None) or str(exc)[:120])
            item = None
    origin = "ai" if item and item.get("_origin") == "ai" else "bank"
    if origin == "ai":
        question, question_snapshot = _staging_question(
            repo.db, item, concept, session.learner_id, session.locale or "vi",
        )
    else:
        item = _fallback_bank(repo.db, concept.concept_id, kind, level,
                              adaptive["start_band"], used)
        if item is None:
            raise AppError(503, "ai_practice_unavailable",
                           "No AI or reviewed bank question is available for this selection.")
        question = item["question"]
        question_snapshot = capture_question(repo, question)
        question_snapshot["source"] = "bank"
        question_snapshot["origin"] = "bank"
    decision = {
        "policy_version": POLICY["version"],
        "origin": origin,
        "question_source": question_snapshot.get("source"),
        "band": adaptive["start_band"],
        "level": level,
        "seq_no": seq,
        "is_fallback": origin != "ai",
        "fallback_reason": fallback_reason,
        "selected_concept_ids": [concept.concept_id],
    }
    attempt = _persist(repo, session, question, question_snapshot, seq, decision)
    # ``assessment_session.config_snapshot`` is immutable by database trigger.
    # Per-question provenance and fallback diagnostics live on the attempt
    # snapshot and selection log instead.
    _prefetch_after(repo, session, seq, kind, level, concept, adaptive, llm is not None)
    return attempt


def _prefetch_after(repo, session, seq, kind, level, concept, adaptive, enabled):
    settings = get_settings()
    if not settings.ai_practice_prefetch or not enabled:
        return
    next_seq = seq + 1
    if next_seq > int(session.config_snapshot.get("max_questions") or 0):
        return
    sequence = adaptive.get("type_sequence") or []
    next_kind = sequence[next_seq - 1] if next_seq - 1 < len(sequence) else kind
    targets = {_next_level(level, True, adaptive["start_band"]),
               _next_level(level, False, adaptive["start_band"])}
    for target in targets:
        key = _cache_key(session.session_id, next_seq, next_kind, target)
        if key in _PREFETCH:
            continue
        thread = threading.Thread(
            target=_prefetch_worker,
            args=(session.session_id, next_seq, next_kind, target, concept.concept_id,
                  adaptive["start_band"], session.locale or "vi", adaptive.get("seed")),
            daemon=True,
            name=f"ai-prefetch-{session.session_id}-{next_seq}-{target}",
        )
        thread.start()


def _prefetch_worker(session_id, seq, kind, level, concept_id, band, locale, request_id):
    from ..db import get_session_factory
    from .llm import build_llm_service
    from .sandbox_runner import build_sandbox_runner
    settings = get_settings()
    try:
        with get_session_factory()() as db:
            concept = db.get(Concept, concept_id)
            if concept is None:
                return
            item = _generate_one(
                db, concept, kind, level, band, locale,
                build_llm_service(settings, db), build_sandbox_runner(settings),
                session_id, seq, settings.ai_practice_timeout_seconds, request_id,
            )
        _store_prefetch(session_id, seq, kind, level, item)
    except Exception as exc:  # background fallback is allowed to stay empty
        LOG.info("AI practice prefetch skipped session=%s seq=%s reason=%s",
                 session_id, seq, type(exc).__name__)


def create(db, learner, payload, concepts, selection, request_id, *, locale, runner=None, llm=None):
    from .question_localization import normalize_locale

    concept = concepts[0]
    band = payload.difficulties[0]
    sequence = _type_sequence(payload)
    settings = get_settings()
    start_level = _start_level(band)
    repo = AssessmentRepository(db)
    concept_row = {
        "concept_id": concept.concept_id, "concept_code": concept.concept_code,
        "concept_name": concept.concept_name, "description": concept.description,
        "subject_area": concept.subject_area, "keywords": concept.keywords,
        "learning_objectives": concept.learning_objectives, "min_difficulty": 1,
        "max_difficulty": 5, "target_pct": "70",
    }
    adaptive = {
        "policy": dict(POLICY), "policy_version": POLICY["version"], "start_band": band,
        "start_level": start_level, "concept_id": concept.concept_id, "seed": str(request_id),
        "timeout_seconds": settings.ai_practice_timeout_seconds,
        "type_sequence": sequence,
        "question_mix": _mix(payload).model_dump(),
    }
    snapshot = {
        "version": 1, "learner_defined": True, "personalized": True, "assembly_mode": "PRACTICE",
        "assessment_id": None, "title": "Luyện tập AI thích ứng",
        "description": "Bài luyện tập thích ứng với câu hỏi do AI tạo.",
        "duration_min": 30, "max_questions": payload.question_count,
        "target_mcq": sequence.count("mcq"), "target_sql": sequence.count("sql"),
        "target_essay": sequence.count("essay"), "question_mix": _mix(payload).model_dump(),
        "result_release_policy": "HUMAN_VERIFIED", "selection": selection, "source": "ai",
        "generation_fallback": False, "ai_generated_count": 0, "generation_diagnostics": [],
        "selected_concept_ids": payload.concept_ids, "difficulty": band,
        "concepts": [concept_row], "question_ids": [], "question_plan": [],
        "adaptive": adaptive, "runner_mode": "ai_adaptive", "result_kind": "estimated_ability",
        "assessment_style": "ADAPTIVE", "purpose": "TEST",
    }
    now = repo.server_time()
    session = repo.create_session(
        None, learner.account_id, now + timedelta(minutes=30), started_at=now,
        locale=normalize_locale(locale), result_release_policy="HUMAN_VERIFIED",
        start_request_id=request_id, purpose="TEST", review_policy="LEGACY",
    )
    session.config_snapshot = snapshot
    db.add(SessionStartRequest(learner_id=learner.account_id, request_id=request_id,
                               session_id=session.session_id))
    _serve(repo, session, [], llm, runner)
    return session


def advance(repo, session, attempts, *, runner=None, llm=None):
    adaptive = (session.config_snapshot or {}).get("adaptive") or {}
    if adaptive.get("policy_version") != POLICY["version"]:
        raise AppError(409, "adaptive_policy_unavailable", "The saved adaptive policy is unavailable")
    attempt = _serve(repo, session, attempts, llm, runner)
    if attempt is None:
        from .assessment_lifecycle import finalize
        finalize(repo.db, session)
    return attempt


def progress(session, attempts):
    adaptive = (session.config_snapshot or {}).get("adaptive") or {}
    if adaptive.get("policy_version") != POLICY["version"]:
        return None
    answered = [attempt for attempt in attempts if attempt.submitted_at is not None]
    level = _level_for(len(answered) + 1, answered, adaptive)
    target = int((session.config_snapshot or {}).get("max_questions") or 0)
    if session.status == "timed_out":
        reason = "time_limit"
    elif session.status == "completed":
        reason = "maximum_questions" if len(answered) >= target else "learner_finished"
    else:
        reason = None
    return {
        "policy_version": POLICY["version"], "band": _band_for(level),
        "ability": float(level), "evidence_count": len(answered), "target_count": target,
        "anchor_count": 0, "minimum_evidence": 1,
        "evidence_sufficient": bool(answered), "stop_reason": reason,
        "inventory_limited": False,
    }


def estimate(session, attempts):
    adaptive = (session.config_snapshot or {}).get("adaptive") or {}
    if adaptive.get("policy_version") != POLICY["version"]:
        return None
    answered = [attempt for attempt in attempts if attempt.submitted_at is not None]
    level = _level_for(len(answered) + 1, answered, adaptive)
    return {"band": _band_for(level), "index": round(level, 2),
            "confidence": "high" if len(answered) >= 8 else "medium" if len(answered) >= 4 else "low",
            "evidence_count": len(answered), "provisional": True}


def _band_for(level):
    for band, (low, high) in DIFFICULTY_BANDS.items():
        if low <= level <= high:
            return band
    return "MEDIUM"


def study_suggestions(db, session):
    adaptive = (session.config_snapshot or {}).get("adaptive") or {}
    if adaptive.get("policy_version") != POLICY["version"] or session.status == "in_progress":
        return []
    from ..repositories import CompetencyRepository
    return [{"concept_id": gap.concept_id, "concept_code": gap.concept.concept_code,
             "concept_name": gap.concept.concept_name, "subject_area": gap.concept.subject_area,
             "reason": "below_target"}
            for gap in CompetencyRepository(db).gaps_for_session(session.session_id)]
