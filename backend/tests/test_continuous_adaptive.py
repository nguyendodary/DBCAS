"""Continuous adaptive MCQ practice: anchors, ability transitions and stop rules."""
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.models import AssessmentSession, Attempt, SelectionLog, SessionQuestionPlan
from app.services.batch_adaptive import POLICY as BATCH_POLICY, next_band
from app.services.continuous_adaptive import band_for, choose, estimate, replay, step
from test_adaptive_engine import _concept, _make_account, _mcq
from test_supervisor_requirements import headers


def setup(db, *, levels=(1, 2, 3, 4, 5), per_level=3):
    admin = _make_account(db, "adaptive-admin@test.dev", "Administrator")
    learner = _make_account(db, "adaptive-learner@test.dev", "Learner")
    concept = _concept(db, "ADAPT-CONT")
    for level in levels:
        for index in range(per_level):
            _mcq(db, concept, diff=level, admin=admin, prompt=f"Level {level}, variant {index}")
    db.commit()
    return admin, learner, concept


def payload(concept, **kw):
    return {"assessment_style": "ADAPTIVE", "concept_ids": [concept.concept_id],
            "difficulties": ["MEDIUM"], "source": "bank", "question_count": 6,
            "request_id": str(uuid4()), **kw}


def start(client, learner, concept, **kw):
    return client.post("/api/v1/practice/start", headers=headers(learner),
                       json=payload(concept, **kw))


def answer(client, db, learner, state, correct=True):
    question = state["current_question"]
    snapshot = db.get(Attempt, question["attempt_id"]).question_snapshot
    option = next(item["option_id"] for item in snapshot["options"] if item["is_correct"] == correct)
    response = client.post(f"/api/v1/sessions/{state['session_id']}/submit", headers=headers(learner),
                           json={"question_id": question["question_id"], "selected_option_id": option})
    assert response.status_code == 200, response.text
    assert response.json()["answer"]["score"] is None
    return response.json()["state"]


def test_start_freezes_inventory_and_serves_three_anchors(client, db_session):
    _, learner, concept = setup(db_session)
    body = payload(concept)
    response = client.post("/api/v1/practice/start", headers=headers(learner), json=body)
    assert response.status_code == 200, response.text
    state = response.json()
    replay_start = client.post("/api/v1/practice/start", headers=headers(learner), json=body)
    assert replay_start.status_code == 200 and replay_start.json()["session_id"] == state["session_id"]
    sid = state["session_id"]
    snapshot = db_session.get(AssessmentSession, sid).config_snapshot
    adaptive = snapshot["adaptive"]
    assert snapshot["runner_mode"] == "adaptive"
    assert snapshot["result_kind"] == "estimated_ability"
    assert snapshot["assessment_style"] == "ADAPTIVE"
    assert snapshot["assembly_mode"] == "PRACTICE"
    assert adaptive["policy_version"] == "continuous-mcq-v1"
    assert adaptive["start_band"] == "MEDIUM" and adaptive["ability"] == 3.0
    assert adaptive["evidence_count"] == 0
    assert len(adaptive["inventory_ids"]) == len(set(adaptive["inventory_ids"]))
    assert len(adaptive["inventory_hash"]) == 64
    assert snapshot["adaptive_inventory_ids"] == adaptive["inventory_ids"]
    assert state["ability_estimate"] == {"band": "MEDIUM", "index": 3.0, "confidence": "low",
                                         "evidence_count": 0, "provisional": True}
    assert "score" not in state["ability_estimate"]
    difficulties = []
    for _ in range(3):
        difficulties.append(state["current_question"]["difficulty_level"])
        state = answer(client, db_session, learner, state)
    assert difficulties == [3, 3, 3]
    assert state["ability_estimate"]["evidence_count"] == 3
    assert state["ability_estimate"]["index"] > 3.0


def test_ability_transitions_are_up_same_or_down():
    assert step(3.0, 3, True, 0) == 3.3
    assert step(3.0, 3, False, 0) == 2.7
    assert band_for(step(3.0, 3, True, 0)) == band_for(step(3.0, 3, False, 0)) == "MEDIUM"
    up = down = 3.0
    for index in range(6):
        up = step(up, 3, True, index)
        down = step(down, 3, False, index)
    assert band_for(up) == "HARD" and up > 3.0
    assert band_for(down) == "EASY" and down < 3.0


def test_seeded_selection_is_reproducible():
    inventory = [{"question_id": index, "difficulty_level": index % 5 + 1} for index in range(1, 21)]

    def picks(rows):
        used, chosen = set(), []
        for _ in range(5):
            question = choose(rows, used, "MEDIUM", 3.0, "fixed-seed")
            used.add(question["question_id"])
            chosen.append(question["question_id"])
        return chosen

    assert picks(inventory) == picks(list(reversed(inventory)))
    assert len(set(picks(inventory))) == 5


def test_run_stops_at_count_and_locks_submitted_answers(client, db_session):
    _, learner, concept = setup(db_session)
    state = start(client, learner, concept).json()
    sid = state["session_id"]
    seen = []
    for _ in range(6):
        seen.append(state["current_question"]["difficulty_level"])
        state = answer(client, db_session, learner, state)
    assert seen[:3] == [3, 3, 3] and max(seen[3:]) > 3
    assert state["status"] == "completed" and state["done"] is True
    assert state["current_question"] is None
    assert state["adaptive_progress"]["stop_reason"] == "maximum_questions"
    assert state["ability_estimate"]["evidence_count"] == 6
    assert state["ability_estimate"]["confidence"] == "medium"
    attempts = list(db_session.scalars(select(Attempt).where(Attempt.session_id == sid)
                                       .order_by(Attempt.seq_no)))
    assert len(attempts) == 6
    assert db_session.scalar(select(func.count()).select_from(SessionQuestionPlan)
                             .where(SessionQuestionPlan.session_id == sid)) == 6
    logs = list(db_session.scalars(select(SelectionLog).where(SelectionLog.session_id == sid)))
    assert len(logs) == 6
    assert all(log.decision_detail["policy_version"] == "continuous-mcq-v1" for log in logs)
    snapshot = attempts[0].question_snapshot
    wrong = next(item["option_id"] for item in snapshot["options"] if not item["is_correct"])
    locked = client.post(f"/api/v1/sessions/{sid}/submit", headers=headers(learner),
                         json={"question_id": attempts[0].question_id, "selected_option_id": wrong})
    assert locked.status_code == 409 and locked.json()["error"]["code"] == "already_submitted"


@pytest.mark.parametrize("levels,per_level", [((3,), 2), ((1, 2), 1)])
def test_inventory_shortage_fails_closed(client, db_session, levels, per_level):
    _, learner, concept = setup(db_session, levels=levels, per_level=per_level)
    response = start(client, learner, concept)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "adaptive_inventory_insufficient"
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 0


def test_inventory_exhaustion_stops_at_the_last_question(client, db_session):
    _, learner, concept = setup(db_session, levels=(3,), per_level=5)
    state = start(client, learner, concept).json()
    for _ in range(5):
        state = answer(client, db_session, learner, state, correct=False)
    assert state["status"] == "completed" and state["answered_count"] == 5
    assert state["adaptive_progress"]["stop_reason"] == "inventory_exhausted"
    assert state["adaptive_progress"]["inventory_limited"] is True
    assert state["ability_estimate"]["band"] == "EASY"
    logs = list(db_session.scalars(select(SelectionLog).where(
        SelectionLog.session_id == state["session_id"]).order_by(SelectionLog.seq_no)))
    assert len(logs) == 5 and logs[-1].is_fallback is True
    assert logs[-1].decision_detail["stop_reason"] == "inventory_exhausted"


def test_result_is_estimated_ability_and_old_batch_policy_is_unchanged(client, db_session):
    _, learner, concept = setup(db_session, levels=(3,), per_level=4)
    state = start(client, learner, concept, question_count=4).json()
    for _ in range(4):
        state = answer(client, db_session, learner, state, correct=False)
    estimate_payload = state["ability_estimate"]
    assert state["result_kind"] == "estimated_ability"
    assert estimate_payload["band"] == "EASY" and estimate_payload["provisional"] is True
    assert estimate_payload["evidence_count"] == 4 and estimate_payload["confidence"] == "medium"
    assert state["study_suggestions"] == [{"concept_id": concept.concept_id,
                                           "concept_code": concept.concept_code,
                                           "concept_name": concept.concept_name,
                                           "subject_area": concept.subject_area,
                                           "reason": "below_target"}]
    summary = next(item for item in client.get("/api/v1/sessions", headers=headers(learner)).json()
                   if item["session_id"] == state["session_id"])
    assert summary["runner_mode"] == "adaptive" and summary["result_kind"] == "estimated_ability"
    assert summary["ability_estimate"]["band"] == "EASY"
    assert summary["overall_result_pct"] is None and summary["concepts"] == []
    cumulative = client.get("/api/v1/sessions/competency/cumulative", headers=headers(learner)).json()
    assert cumulative["concepts"] == [] and cumulative["gaps"] == []
    evidence = client.get(f"/api/v1/sessions/{state['session_id']}/evidence", headers=headers(learner)).json()
    assert evidence["result_kind"] == "estimated_ability"
    assert evidence["ability_estimate"] == estimate_payload
    assert evidence["study_suggestions"][0]["reason"] == "below_target"
    assert "score" not in evidence["ability_estimate"] and "official" not in str(evidence["ability_estimate"])
    assert BATCH_POLICY["version"] == "mcq-batch-v1"
    assert next_band("MEDIUM", Decimal("0.8")) == "HARD"


def test_replay_ignores_unanswered_and_human_display_grades(client, db_session):
    _, learner, concept = setup(db_session)
    state = start(client, learner, concept, question_count=3).json()
    state = answer(client, db_session, learner, state)
    attempts = list(db_session.scalars(select(Attempt).where(
        Attempt.session_id == state["session_id"]).order_by(Attempt.seq_no)))
    before = replay(attempts, "MEDIUM")
    attempts[0].grading_detail = {"grader": "human_verified", "is_correct": False}
    attempts[0].score = Decimal("0")
    assert replay(attempts, "MEDIUM") == before
    state = answer(client, db_session, learner, state)
    state = answer(client, db_session, learner, state)
    assert state["ability_estimate"]["evidence_count"] == 3
    db_session.rollback()
    db_session.expire_all()
    attempts = list(db_session.scalars(select(Attempt).where(
        Attempt.session_id == state["session_id"]).order_by(Attempt.seq_no)))
    assert estimate(db_session.get(AssessmentSession, state["session_id"]), attempts)["evidence_count"] == 3
