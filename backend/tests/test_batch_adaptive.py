"""Optional batch practice: real persistence, frozen evidence and boundaries."""
from datetime import timedelta
from copy import deepcopy
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import AdaptiveEvent, AssessmentSession, Attempt, SelectionLog, SessionQuestionPlan
from app.services.batch_adaptive import choose, next_band
from app.services.cumulative_competency import is_official
from test_adaptive_engine import _make_account, _concept, _mcq, _assessment
from test_supervisor_requirements import headers


def setup(db, *, levels=(1, 3, 4), per_level=6, policy="IMMEDIATE"):
    admin = _make_account(db, "batch-admin@test.dev", "Administrator")
    learner = _make_account(db, "batch-learner@test.dev", "Learner")
    concept = _concept(db, "SQL-SELECT")
    for level in levels:
        for index in range(per_level):
            _mcq(db, concept, diff=level, admin=admin, prompt=f"MCQ level {level}, variant {index}")
    assessment = _assessment(db, admin, [concept], status="published", complete=False)
    assessment.result_release_policy = policy
    db.commit()
    payload = {"concept_ids": [concept.concept_id], "difficulty": "EASY", "mode": "ADAPTIVE", "request_id": str(uuid4())}
    return admin, learner, assessment, payload


def start(client, learner, assessment, payload):
    return client.post(f"/api/v1/assessments/{assessment.assessment_id}/sessions", json=payload, headers=headers(learner))


def answer(client, db, learner, state, correct=True):
    q = state["current_question"]
    snapshot = db.get(Attempt, q["attempt_id"]).question_snapshot
    option = next(o["option_id"] for o in snapshot["options"] if o["is_correct"] == correct)
    response = client.post(f"/api/v1/sessions/{state['session_id']}/submit", headers=headers(learner),
                           json={"question_id": q["question_id"], "selected_option_id": option})
    assert response.status_code == 200, response.json()
    if state["result_release_policy"] == "HUMAN_VERIFIED":
        assert response.json()["answer"]["score"] is None
        assert response.json()["answer"]["is_correct"] is None
    return response.json()["state"]


@pytest.mark.parametrize("band,ratio,expected", [("EASY", ".8", "MEDIUM"), ("MEDIUM", ".8", "HARD"),
    ("HARD", "1", "HARD"), ("HARD", ".4", "MEDIUM"), ("MEDIUM", ".4", "EASY"),
    ("EASY", "0", "EASY"), ("MEDIUM", ".6", "MEDIUM")])
def test_rule_boundaries(band, ratio, expected):
    assert next_band(band, Decimal(ratio)) == expected


def test_reproducible_fallback_without_repetition():
    pool = [{"question_id": i, "difficulty_level": i % 5 + 1} for i in range(20)]
    picked = choose(pool, {0, 1}, "MEDIUM", 5, "fixed-intent")
    assert picked == choose(list(reversed(pool)), {0, 1}, "MEDIUM", 5, "fixed-intent")
    assert len({q["question_id"] for q in picked}) == 5
    assert not {q["question_id"] for q in picked} & {0, 1}
    assert all(q["difficulty_level"] == 3 for q in picked[:4])


@pytest.mark.parametrize("policy", ["IMMEDIATE", "HUMAN_VERIFIED"])
def test_batches_progress_finish_and_preserve_snapshots(client, db_session, policy):
    _, learner, assessment, payload = setup(db_session, policy=policy)
    response = start(client, learner, assessment, payload)
    assert response.status_code == 201, response.json()
    state = response.json()
    sid = state["session_id"]
    frozen = deepcopy(db_session.get(AssessmentSession, sid).config_snapshot)
    assert state["adaptive_progress"]["batch_size"] == 5
    assert state["adaptive_progress"]["band"] == "EASY"
    assert "inventory" not in state["adaptive_progress"] and "is_correct" not in str(state)
    retry = start(client, learner, assessment, payload)
    assert retry.json()["session_id"] == sid
    seen, bands = [], []
    for index in range(13):
        seen.append(state["current_question"]["question_id"])
        bands.append(state["adaptive_progress"]["band"])
        state = answer(client, db_session, learner, state)
        if index < 4:
            assert state["adaptive_progress"]["round"] == 1
        if index == 4:
            assert state["adaptive_progress"]["round"] == 2
            assert state["adaptive_progress"]["band"] == "MEDIUM"
        if index == 9:
            assert state["adaptive_progress"]["round"] == 3
            assert state["adaptive_progress"]["band"] == "HARD"
    assert len(set(seen)) == 13
    assert bands == ["EASY"] * 5 + ["MEDIUM"] * 5 + ["HARD"] * 3
    assert state["status"] == "completed" and state["done"] and not state["current_question"]
    assert state["adaptive_progress"]["stop_reason"] == "maximum_questions"
    assert state["adaptive_progress"]["evidence_sufficient"]
    session = db_session.get(AssessmentSession, sid)
    db_session.refresh(session)
    assert session.config_snapshot == frozen
    assert not is_official(session)
    assert session.config_snapshot["adaptive"]["policy"]["version"] == "mcq-batch-v1"
    assert db_session.query(AdaptiveEvent).filter_by(session_id=sid, event_type="decision").count() == 3
    planned = list(db_session.scalars(select(SessionQuestionPlan).where(SessionQuestionPlan.session_id == sid).order_by(SessionQuestionPlan.seq_no)))
    assert [p.question_id for p in planned] == seen
    logs = list(db_session.scalars(select(SelectionLog).where(SelectionLog.session_id == sid)))
    assert len(logs) == 13 and all(log.decision_detail["policy_version"] == "mcq-batch-v1" for log in logs)
    evidence = client.get(f"/api/v1/sessions/{sid}/evidence", headers=headers(learner))
    assert evidence.status_code == (409 if policy == "HUMAN_VERIFIED" else 200)
    profile = client.get("/api/v1/sessions/competency/cumulative", headers=headers(learner)).json()
    assert profile["concepts"] == [] and profile["gaps"] == []
    # Later human corrections must not erase the original routing evidence.
    for attempt in db_session.query(Attempt).filter_by(session_id=sid):
        attempt.grading_detail = {**attempt.grading_detail, "grader": "human_verified"}
    db_session.commit()
    later = client.get(f"/api/v1/sessions/{sid}", headers=headers(learner)).json()
    assert later["adaptive_progress"]["evidence_sufficient"]


def test_stable_performance_stops_at_ten(client, db_session):
    _, learner, assessment, payload = setup(db_session, levels=(4,), per_level=15)
    payload["difficulty"] = "HARD"
    state = start(client, learner, assessment, payload).json()
    for _ in range(10):
        state = answer(client, db_session, learner, state)
    assert state["status"] == "completed"
    assert state["answered_count"] == 10
    assert state["adaptive_progress"]["stop_reason"] == "stable_performance"


@pytest.mark.parametrize("available", [4, 7])
def test_minimum_inventory_and_safe_exhaustion(client, db_session, available):
    _, learner, assessment, payload = setup(db_session, levels=(1,), per_level=available)
    response = start(client, learner, assessment, payload)
    if available < 5:
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "adaptive_inventory_insufficient"
        assert db_session.query(AssessmentSession).count() == 0
    else:
        state = response.json()
        for _ in range(available):
            state = answer(client, db_session, learner, state)
        assert state["status"] == "completed"
        assert state["adaptive_progress"]["stop_reason"] == "inventory_exhausted"
        assert state["adaptive_progress"]["inventory_limited"]


def test_early_finish_is_explicitly_insufficient_and_time_is_authoritative(client, db_session):
    _, learner, assessment, payload = setup(db_session)
    state = start(client, learner, assessment, payload).json()
    state = answer(client, db_session, learner, state)
    final = client.post(f"/api/v1/sessions/{state['session_id']}/finish", headers=headers(learner)).json()
    assert final["adaptive_progress"]["stop_reason"] == "learner_finished"
    assert not final["adaptive_progress"]["evidence_sufficient"]
    payload["request_id"] = str(uuid4())
    state = start(client, learner, assessment, payload).json()
    row = db_session.get(AssessmentSession, state["session_id"])
    row.expires_at = row.started_at - timedelta(seconds=1)
    db_session.commit()
    timed_out = client.get(f"/api/v1/sessions/{state['session_id']}", headers=headers(learner)).json()
    assert timed_out["status"] == "timed_out"
    assert timed_out["adaptive_progress"]["stop_reason"] == "time_limit"


def test_other_learner_cannot_read_or_advance(client, db_session):
    _, learner, assessment, payload = setup(db_session)
    state = start(client, learner, assessment, payload).json()
    other = _make_account(db_session, "other-batch@test.dev", "Learner")
    db_session.commit()
    for method, suffix in (("get", ""), ("get", "/questions"), ("post", "/serve-next"), ("post", "/finish")):
        response = getattr(client, method)(f"/api/v1/sessions/{state['session_id']}{suffix}", headers=headers(other))
        assert response.status_code == 404


def test_unfinalized_or_ai_evidence_cannot_drive_the_next_batch(client, db_session):
    from app.schemas import SubmitAnswerRequest
    from app.services.grading_service import submit_answer
    _, learner, assessment, payload = setup(db_session)
    state = start(client, learner, assessment, payload).json()
    for _ in range(4):
        state = answer(client, db_session, learner, state)
    q = state["current_question"]
    attempt = db_session.get(Attempt, q["attempt_id"])
    correct = next(o["option_id"] for o in attempt.question_snapshot["options"] if o["is_correct"])
    submit_answer(db_session, state["session_id"], learner, SubmitAnswerRequest(question_id=q["question_id"], selected_option_id=correct))
    attempt.grading_detail = {**attempt.grading_detail, "grader": "llm_rubric"}
    db_session.commit()
    response = client.post(f"/api/v1/sessions/{state['session_id']}/serve-next", headers=headers(learner))
    assert response.status_code == 409 and response.json()["error"]["code"] == "adaptive_evidence_pending"
    assert db_session.query(AdaptiveEvent).filter_by(session_id=state["session_id"], event_type="batch").count() == 1


def test_adaptive_events_and_snapshots_are_immutable(client, db_session):
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    _, learner, assessment, payload = setup(db_session)
    sid = start(client, learner, assessment, payload).json()["session_id"]
    for statement in ("UPDATE adaptive_event SET payload='{}' WHERE session_id=:id",
                      "DELETE FROM adaptive_event WHERE session_id=:id",
                      "UPDATE assessment_session SET config_snapshot='{}' WHERE session_id=:id"):
        with pytest.raises(DBAPIError):
            with db_session.begin_nested():
                db_session.execute(text(statement), {"id": sid})
