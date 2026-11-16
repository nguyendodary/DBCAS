"""Continuous adaptive MCQ practice: bank-only, sequential, estimated ability.

Separate from ``mcq-batch-v1`` so historical batch sessions keep their frozen
five-answer rules. Every answer updates a transparent running ability index on
the 1..5 difficulty scale; three anchors stay at the starting band, then each
next question is the nearest frozen-bank item to the updated ability.
"""
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
from types import SimpleNamespace
import json

from sqlalchemy import select

from ..errors import AppError
from ..models import Question, SessionQuestionPlan, SessionStartRequest
from ..repositories import AssessmentRepository, QuestionRepository
from .blueprints import DIFFICULTY_BANDS

POLICY = {
    "version": "continuous-mcq-v1",
    "anchor_count": 3,
    "question_types": ["mcq"],
    "ability_min": 1.0, "ability_max": 5.0,
    "band_midpoints": {"EASY": 1.5, "MEDIUM": 3.0, "HARD": 4.5},
    "k_start": 0.6, "k_end": 0.2, "k_decay_answers": 10,
    "confidence_medium": 4, "confidence_high": 8,
}
BANDS = ("EASY", "MEDIUM", "HARD")


def expected_outcome(difficulty, ability):
    """Logistic expected success, p = 1 / (1 + 10 ** ((difficulty - a) / 2))."""
    return 1.0 / (1.0 + 10.0 ** ((difficulty - ability) / 2.0))


def learning_rate(evidence_count):
    """K decays linearly from 0.6 to 0.2 over the first ten answers."""
    span = POLICY["k_start"] - POLICY["k_end"]
    value = POLICY["k_start"] - span * min(evidence_count, POLICY["k_decay_answers"]) / POLICY["k_decay_answers"]
    return round(max(POLICY["k_end"], value), 4)


def step(ability, difficulty, correct, evidence_count):
    """One documented ability update, clamped to the 1..5 scale."""
    k = learning_rate(evidence_count)
    value = ability + k * ((1.0 if correct else 0.0) - expected_outcome(difficulty, ability))
    return round(min(POLICY["ability_max"], max(POLICY["ability_min"], value)), 4)


def band_for(ability):
    return min(BANDS, key=lambda band: (abs(POLICY["band_midpoints"][band] - ability), BANDS.index(band)))


def confidence_for(evidence_count):
    if evidence_count >= POLICY["confidence_high"]:
        return "high"
    if evidence_count >= POLICY["confidence_medium"]:
        return "medium"
    return "low"


def _answered(attempt):
    return (attempt.submitted_at is not None
            and (attempt.grading_detail or {}).get("grader") != "unanswered"
            and (attempt.question_snapshot or {}).get("question_type") == "mcq")


def _correct(attempt):
    options = attempt.question_snapshot.get("options", [])
    correct_id = next((option["option_id"] for option in options if option.get("is_correct")), None)
    return attempt.selected_option_id is not None and attempt.selected_option_id == correct_id


def replay(attempts, start_band):
    """Derive ability and evidence from submitted answers only."""
    ability, evidence = POLICY["band_midpoints"][start_band], 0
    for attempt in sorted(attempts, key=lambda item: item.seq_no):
        if not _answered(attempt):
            continue
        ability = step(ability, int(attempt.question_snapshot["difficulty_level"]), _correct(attempt), evidence)
        evidence += 1
    return ability, evidence


def estimate(session, attempts):
    adaptive = (session.config_snapshot or {}).get("adaptive") or {}
    if adaptive.get("policy_version") != POLICY["version"]:
        return None
    ability, evidence = replay(attempts, adaptive["start_band"])
    return {"band": band_for(ability), "index": round(ability, 2),
            "confidence": confidence_for(evidence), "evidence_count": evidence, "provisional": True}


def progress(session, attempts):
    """Public progress: no inventory content, answer keys or grade evidence."""
    adaptive = (session.config_snapshot or {}).get("adaptive") or {}
    if adaptive.get("policy_version") != POLICY["version"]:
        return None
    ability, evidence = replay(attempts, adaptive["start_band"])
    target = (session.config_snapshot or {}).get("max_questions", 0)
    if session.status == "timed_out":
        reason = "time_limit"
    elif session.status == "completed":
        if len(attempts) >= target:
            reason = "maximum_questions"
        elif len(attempts) >= len(adaptive.get("inventory_ids", [])):
            reason = "inventory_exhausted"
        else:
            reason = "learner_finished"
    else:
        reason = None
    return {"policy_version": POLICY["version"], "band": band_for(ability),
            "ability": round(ability, 2), "evidence_count": evidence, "target_count": target,
            "anchor_count": POLICY["anchor_count"], "minimum_evidence": POLICY["anchor_count"],
            "evidence_sufficient": evidence >= POLICY["anchor_count"],
            "stop_reason": reason, "inventory_limited": reason == "inventory_exhausted"}


def choose(inventory, used, band, ability, seed):
    """Nearest band then nearest ability; reproducible hash breaks ties."""
    low, high = DIFFICULTY_BANDS[band]
    available = [question for question in inventory if question["question_id"] not in used]
    if not available:
        return None

    def key(question):
        level = question["difficulty_level"]
        outside = max(low - level, level - high, 0)
        tie = sha256(f'{seed}:{question["question_id"]}'.encode()).hexdigest()
        return outside, abs(level - ability), tie

    return min(available, key=key)


def build_inventory(db, concept, start_band):
    """Freeze validated, distinct-family MCQs for one concept; fail closed."""
    from .adaptive_engine import _eligible_pool
    from .evidence_context import capture_question
    from .question_service import _validation_missing

    repo = AssessmentRepository(db)
    target = {"concept_id": concept.concept_id, "min_difficulty": 1, "max_difficulty": 5}
    config = SimpleNamespace(assessment_id=None, targets=[SimpleNamespace(**target)])
    pool = [(question, fits) for question, fits in _eligible_pool(config, set(), repo)
            if question.question_type == "mcq" and question.source == "bank"]
    ids = sorted(question.question_id for question, _ in pool)
    db.execute(select(Question.question_id).where(Question.question_id.in_(ids))
               .order_by(Question.question_id).with_for_update(read=True)).all()
    bank = QuestionRepository(db)
    inventory, families = [], set()
    for question_id in ids:
        question = db.scalar(select(Question).where(Question.question_id == question_id)
                             .options(*bank._detail_loads()).execution_options(populate_existing=True))
        if (question is None or question.status != "validated" or question.source != "bank"
                or question.question_type != "mcq" or _validation_missing(bank, question)
                or not any(tag.confirmed and tag.concept_id == concept.concept_id for tag in question.concept_tags)):
            raise AppError(409, "question_bank_changed", "The question bank changed. Retry assessment creation.")
        family = question.family_id or question.question_id
        if family not in families:
            families.add(family)
            inventory.append(capture_question(repo, question))
    low, high = DIFFICULTY_BANDS[start_band]
    anchors = [item for item in inventory if low <= item["difficulty_level"] <= high]
    if len(anchors) < POLICY["anchor_count"]:
        raise AppError(422, "adaptive_inventory_insufficient",
                       f"Adaptive practice needs at least {POLICY['anchor_count']} approved MCQs in the "
                       "selected starting difficulty for one skill. Choose another starting difficulty or use Practice.")
    return inventory


def _serve(repo, session, attempts, inventory):
    snapshot = session.config_snapshot
    adaptive = snapshot["adaptive"]
    target = snapshot["max_questions"]
    seq = len(attempts) + 1
    if seq > target:
        return None
    ability, evidence = replay(attempts, adaptive["start_band"])
    used = {attempt.question_id for attempt in attempts}
    phase = "anchor" if seq <= adaptive["anchor_count"] else "adaptive"
    band = adaptive["start_band"] if phase == "anchor" else band_for(ability)
    question = choose(inventory, used, band, ability, adaptive["seed"])
    if question is None:
        return None
    low, high = DIFFICULTY_BANDS[band]
    remaining = any(item["question_id"] not in used and item["question_id"] != question["question_id"]
                    for item in inventory)
    stop_reason = ("maximum_questions" if seq == target
                   else "inventory_exhausted" if not remaining else None)
    decision = {"phase": phase, "policy_version": POLICY["version"], "band": band,
                "ability": round(ability, 4), "evidence_count": evidence,
                "served_difficulty": question["difficulty_level"],
                "is_fallback": not low <= question["difficulty_level"] <= high,
                "inventory_hash": adaptive["inventory_hash"], "stop_reason": stop_reason,
                "selected_concept_ids": snapshot.get("selected_concept_ids", [])}
    repo.db.add(SessionQuestionPlan(session_id=session.session_id, seq_no=seq,
                                    question_id=question["question_id"]))
    attempt = repo.create_attempt(session.session_id, question["question_id"], seq)
    attempt.question_snapshot = deepcopy(question)
    repo.create_selection_log(session.session_id, seq, question["question_id"],
                              is_fallback=decision["is_fallback"], decision_detail=decision)
    return attempt


def advance(repo, session, attempts):
    """Serve the next frozen-bank question, or finalize the session."""
    adaptive = (session.config_snapshot or {}).get("adaptive") or {}
    if adaptive.get("policy_version") != POLICY["version"]:
        raise AppError(409, "adaptive_policy_unavailable", "The saved adaptive policy is unavailable")
    attempt = _serve(repo, session, attempts, adaptive["inventory"])
    if attempt is None:
        from .assessment_lifecycle import finalize
        finalize(repo.db, session)
    return attempt


def create(db, learner, payload, concepts, selection, request_id, *, locale):
    """Create the frozen adaptive session and serve anchor question one."""
    from .question_localization import normalize_locale

    concept = concepts[0]
    start_band = payload.difficulties[0]
    inventory = build_inventory(db, concept, start_band)
    repo = AssessmentRepository(db)
    ability = POLICY["band_midpoints"][start_band]
    concept_row = {
        "concept_id": concept.concept_id, "concept_code": concept.concept_code,
        "concept_name": concept.concept_name, "description": concept.description,
        "subject_area": concept.subject_area, "keywords": concept.keywords,
        "learning_objectives": concept.learning_objectives, "min_difficulty": 1,
        "max_difficulty": 5, "target_pct": "70",
    }
    adaptive = {"policy": dict(POLICY), "policy_version": POLICY["version"], "start_band": start_band,
                "anchor_count": POLICY["anchor_count"], "ability": ability,
                "evidence_count": 0, "seed": request_id,
                "inventory": inventory, "inventory_ids": [item["question_id"] for item in inventory],
                "inventory_hash": sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest()}
    snapshot = {
        "version": 1, "learner_defined": True, "personalized": True, "assembly_mode": "PRACTICE",
        "assessment_id": None, "title": "Luyện tập tự chọn",
        "description": "Bài luyện tập theo lựa chọn của bạn.",
        "duration_min": 30, "max_questions": payload.question_count,
        "target_mcq": payload.question_count, "target_sql": 0, "target_essay": 0,
        "question_mix": payload.question_mix.model_dump() if payload.question_mix is not None else None,
        "result_release_policy": "HUMAN_VERIFIED", "selection": selection, "source": "bank",
        "generation_fallback": False, "bank_mixed": False, "template_fallback": False,
        "ai_generated_count": 0, "generation_diagnostics": [], "selection_notice": None,
        "coverage_notice": None, "uncovered_concepts": [], "selection_provenance": [],
        "selected_concept_ids": payload.concept_ids, "difficulty": start_band,
        "concepts": [concept_row], "question_ids": [], "question_plan": [],
        "adaptive_inventory_ids": [item["question_id"] for item in inventory],
        "adaptive": adaptive, "runner_mode": "adaptive", "result_kind": "estimated_ability",
        "assessment_style": "ADAPTIVE",
    }
    now = repo.server_time()
    session = repo.create_session(None, learner.account_id, now + timedelta(minutes=30),
                                  started_at=now, locale=normalize_locale(locale),
                                  result_release_policy="HUMAN_VERIFIED", start_request_id=request_id)
    session.config_snapshot = snapshot
    db.add(SessionStartRequest(learner_id=learner.account_id, request_id=request_id,
                               session_id=session.session_id))
    _serve(repo, session, [], inventory)
    return session


def study_suggestions(db, session):
    """Reuse the existing below-benchmark gap rows as study suggestions."""
    adaptive = (session.config_snapshot or {}).get("adaptive") or {}
    if adaptive.get("policy_version") != POLICY["version"] or session.status == "in_progress":
        return []
    from ..repositories import CompetencyRepository
    return [{"concept_id": gap.concept_id, "concept_code": gap.concept.concept_code,
             "concept_name": gap.concept.concept_name, "subject_area": gap.concept.subject_area,
             "reason": "below_target"}
            for gap in CompetencyRepository(db).gaps_for_session(session.session_id)]
