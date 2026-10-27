"""Optional low-stakes adaptive practice; transparent rules, no IRT claims.

Only deterministic, submitted MCQ answer-key grades drive decisions. The
inventory and policy are frozen at start; human/AI grades never drive routing.
Formal/legacy selection and official cumulative competency remain independent.
"""
from copy import deepcopy
from datetime import timedelta
from decimal import Decimal
from hashlib import sha256
import json
from types import SimpleNamespace

from sqlalchemy import select

from ..errors import AppError
from ..models import AdaptiveEvent, Question, SessionQuestionPlan, SessionStartRequest
from ..repositories import QuestionRepository
from .blueprints import DIFFICULTY_BANDS
from .evidence_context import capture_question

POLICY = {"version": "mcq-batch-v1", "batch_size": 5, "minimum_evidence": 5,
          "maximum_questions": 13, "raise_at": "0.80", "lower_at": "0.40",
          "stable_minimum": 10, "question_types": ["mcq"]}
BANDS = ("EASY", "MEDIUM", "HARD")


def _state(session):
    frozen = (session.config_snapshot or {}).get("adaptive")
    if not frozen:
        return None
    events = sorted(session.adaptive_events, key=lambda e: e.round_no)
    batches = [e.payload for e in events if e.event_type == "batch"]
    decisions = [e.payload for e in events if e.event_type == "decision"]
    return {**frozen, "batches": batches, "decisions": decisions,
            "band": batches[-1]["band"] if batches else session.config_snapshot["difficulty"],
            "stop_reason": decisions[-1].get("stop_reason") if decisions else None}


def _event(session, round_no, kind, payload):
    session.adaptive_events.append(AdaptiveEvent(session_id=session.session_id, round_no=round_no,
                                               event_type=kind, payload=deepcopy(payload)))


def next_band(band, ratio):
    index = BANDS.index(band)
    if ratio >= Decimal(POLICY["raise_at"]):
        index = min(index + 1, 2)
    elif ratio <= Decimal(POLICY["lower_at"]):
        index = max(index - 1, 0)
    return BANDS[index]


def choose(inventory, used, band, count, seed):
    """Nearest allowed band, then reproducible tie breaking; no family repeats."""
    low, high = DIFFICULTY_BANDS[band]
    ordered = sorted((q for q in inventory if q["question_id"] not in used), key=lambda q: (
        max(low - q["difficulty_level"], q["difficulty_level"] - high, 0),
        sha256(f'{seed}:{q["question_id"]}'.encode()).hexdigest()))
    return ordered[:count]


def start(db, repo, assessment, learner, payload, snapshot, *, locale):
    from .adaptive_engine import _eligible_pool, _state
    from .question_localization import normalize_locale
    from .question_service import _validation_missing
    snapshot["concepts"] = [c for c in snapshot["concepts"] if c["concept_id"] in payload.concept_ids]
    target = snapshot["concepts"][0]
    low, high = DIFFICULTY_BANDS[payload.difficulty]
    if target["min_difficulty"] > high or target["max_difficulty"] < low:
        raise AppError(422, "adaptive_difficulty_unavailable", "This skill does not allow the selected initial difficulty")
    config = SimpleNamespace(**{**snapshot, "targets": [SimpleNamespace(**c) for c in snapshot["concepts"]]})
    pool = [(q, fits) for q, fits in _eligible_pool(config, set(), repo) if q.question_type == "mcq"]
    bank = QuestionRepository(db)
    ids = sorted(q.question_id for q, _ in pool)
    db.execute(select(Question.question_id).where(Question.question_id.in_(ids))
               .order_by(Question.question_id).with_for_update(read=True)).all()
    inventory, families = [], set()
    for qid in ids:
        q = db.scalar(select(Question).where(Question.question_id == qid)
                      .options(*bank._detail_loads()).execution_options(populate_existing=True))
        if (q.status != "validated" or q.question_type != "mcq" or _validation_missing(bank, q)
                or not target["min_difficulty"] <= q.difficulty_level <= target["max_difficulty"]
                or not any(t.confirmed and t.concept_id == target["concept_id"] for t in q.concept_tags)):
            raise AppError(409, "question_bank_changed", "The question bank changed. Retry assessment creation.")
        family = q.family_id or q.question_id
        if family not in families:
            families.add(family)
            inventory.append(capture_question(repo, q))
    if len(inventory) < POLICY["minimum_evidence"]:
        raise AppError(422, "adaptive_inventory_insufficient",
                       "Adaptive practice needs at least five distinct approved MCQs for one skill. Use Practice for this selection.")
    if not any(low <= q["difficulty_level"] <= high for q in inventory):
        raise AppError(422, "adaptive_difficulty_unavailable", "No approved MCQ is available at the selected initial difficulty. Use Practice or another difficulty.")
    maximum = min(assessment.max_questions, POLICY["maximum_questions"])
    if maximum < POLICY["minimum_evidence"]:
        raise AppError(422, "adaptive_inventory_insufficient", "This assessment is too short for adaptive practice. Use Practice.")
    seed = str(payload.request_id)
    snapshot.update(personalized=True, assembly_mode="ADAPTIVE", selected_concept_ids=sorted(payload.concept_ids),
                    difficulty=payload.difficulty, requested_question_count=payload.question_count,
                    max_questions=maximum, target_mcq=maximum, target_sql=0, target_essay=0,
                    adaptive_inventory_ids=[q["question_id"] for q in inventory],
                    adaptive={"policy": dict(POLICY), "seed": seed, "inventory": inventory,
                              "inventory_hash": sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest(),
                              })
    now = repo.server_time()
    session = repo.create_session(assessment.assessment_id, learner.account_id,
        now + timedelta(minutes=assessment.duration_min), started_at=now, locale=normalize_locale(locale),
        result_release_policy=assessment.result_release_policy, start_request_id=seed)
    session.config_snapshot = snapshot
    db.add(SessionStartRequest(learner_id=learner.account_id, request_id=seed, session_id=session.session_id))
    _append_batch(repo, session, [], payload.difficulty)
    _serve(repo, session, 1)
    db.commit()
    return _state(repo, session)


def _append_batch(repo, session, attempts, band):
    config = session.config_snapshot
    state = _state(session)
    used = {a.question_id for a in attempts}
    remaining = config["max_questions"] - len(used)
    chosen = choose(state["inventory"], used, band, min(state["policy"]["batch_size"], remaining), state["seed"])
    low, high = DIFFICULTY_BANDS[band]
    batch = {"round": len(state["batches"]) + 1, "band": band,
             "question_ids": [q["question_id"] for q in chosen],
             "fallback_ids": [q["question_id"] for q in chosen if not low <= q["difficulty_level"] <= high],
             "start_seq": len(attempts) + 1}
    _event(session, batch["round"], "batch", batch)
    repo.db.add_all([SessionQuestionPlan(session_id=session.session_id, seq_no=len(attempts) + index,
                                         question_id=q["question_id"]) for index, q in enumerate(chosen, 1)])
    return batch


def _serve(repo, session, seq):
    state = _state(session)
    batch = state["batches"][-1]
    qid = batch["question_ids"][seq - batch["start_seq"]]
    snapshot = next(q for q in state["inventory"] if q["question_id"] == qid)
    attempt = repo.create_attempt(session.session_id, qid, seq)
    attempt.question_snapshot = deepcopy(snapshot)
    repo.create_selection_log(session.session_id, seq, qid, is_fallback=qid in batch["fallback_ids"],
        decision_detail={"phase": "adaptive_batch", "policy_version": state["policy"]["version"],
                         "round": batch["round"], "band": batch["band"],
                         "inventory_hash": state["inventory_hash"], "served_difficulty": snapshot["difficulty_level"]})
    return attempt


def advance(repo, session, attempts):
    config = session.config_snapshot
    state = _state(session)
    if state["policy"]["version"] != POLICY["version"]:
        raise AppError(409, "adaptive_policy_unavailable", "The saved adaptive policy is unavailable")
    batch = state["batches"][-1]
    if len(attempts) < batch["start_seq"] + len(batch["question_ids"]) - 1:
        return _serve(repo, session, len(attempts) + 1)
    evidence = [a for a in attempts if a.question_id in batch["question_ids"]]
    if len(evidence) != len(batch["question_ids"]) or any(
        a.submitted_at is None or a.grading_status != "graded" or a.score is None
        or (a.grading_detail or {}).get("grader") != "answer_key"
        or (a.question_snapshot or {}).get("question_type") != "mcq" for a in evidence):
        raise AppError(409, "adaptive_evidence_pending", "The batch needs finalized answer-key evidence before continuing")
    possible = sum(Decimal(a.question_snapshot["points"]) for a in evidence)
    ratio = sum(a.score for a in evidence) / possible
    following = next_band(state["band"], ratio)
    decision = {"round": batch["round"], "from_band": state["band"], "next_band": following,
                "ratio": str(ratio), "attempt_ids": [a.attempt_id for a in evidence],
                "scores": [str(a.score) for a in evidence],
                "submission_hashes": [a.submission_hash for a in evidence]}
    state["decisions"].append(decision)
    reason = None
    used = {a.question_id for a in attempts}
    if len(attempts) >= config["max_questions"]:
        reason = "maximum_questions"
    elif not any(q["question_id"] not in used for q in state["inventory"]):
        reason = "inventory_exhausted"
    elif (len(attempts) >= state["policy"]["stable_minimum"] and len(state["decisions"]) >= 2
          and all(d["from_band"] == d["next_band"] == following for d in state["decisions"][-2:])
          and not any(b["fallback_ids"] for b in state["batches"][-2:])):
        reason = "stable_performance"
    decision["stop_reason"] = reason
    decision["policy_version"] = state["policy"]["version"]
    _event(session, batch["round"], "decision", decision)
    if reason:
        from .assessment_lifecycle import finalize
        finalize(repo.db, session)
        return None
    _append_batch(repo, session, attempts, following)
    return _serve(repo, session, len(attempts) + 1)


def progress(session, attempts):
    """Public progress deliberately excludes inventory, keys and grade evidence."""
    state = _state(session)
    if not state:
        return None
    batch = state["batches"][-1]
    # Human review can replace the display grade later. Completed routing
    # evidence remains the immutable answer-key decision recorded at the time.
    finalized_ids = {aid for decision in state["decisions"] for aid in decision["attempt_ids"]}
    finalized_ids.update(a.attempt_id for a in attempts if a.submitted_at is not None
                         and a.grading_status == "graded" and (a.grading_detail or {}).get("grader") == "answer_key")
    count = len(finalized_ids)
    reason = state.get("stop_reason")
    if session.status != "in_progress" and reason is None:
        reason = "time_limit" if session.status == "timed_out" else "learner_finished"
    return {"policy_version": state["policy"]["version"], "round": batch["round"],
            "batch_size": len(batch["question_ids"]), "band": batch["band"],
            "batch_answered": sum(a.submitted_at is not None and a.question_id in batch["question_ids"] for a in attempts),
            "minimum_evidence": state["policy"]["minimum_evidence"],
            "evidence_sufficient": count >= state["policy"]["minimum_evidence"],
            "inventory_limited": bool(any(b["fallback_ids"] for b in state["batches"])) or reason == "inventory_exhausted",
            "stop_reason": reason}
