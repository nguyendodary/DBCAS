"""New practice contracts against PostgreSQL and the real SELECT sandbox."""
from copy import deepcopy
from uuid import uuid4
from decimal import Decimal
import pytest
from sqlalchemy import select, func

from app.models import Assessment, AssessmentSession, Attempt, GradeEditAudit, EvaluationRecord
from app.services import evaluation_service as evaluations, practice_service as practice
from app.services.system_settings import update_flow
from test_adaptive_engine import _make_account, _concept, _mcq, _sql, _essay
from test_supervisor_requirements import headers


def fixture(db):
    admin = _make_account(db, "practice-admin@test.dev", "Administrator")
    learner = _make_account(db, "practice-learner@test.dev", "Learner")
    concepts = [_concept(db, f"PRACTICE-{i}") for i in range(2)]
    for concept in concepts:
        for level in range(1, 6): _mcq(db, concept, diff=level, admin=admin)
    _sql(db, concepts[0], admin=admin)
    _essay(db, concepts[0], admin=admin)
    db.commit()
    return admin, learner, concepts


def selection(concepts, **kw):
    return dict(concept_ids=[c.concept_id for c in concepts], difficulties=["EASY", "MEDIUM", "HARD"],
                source="bank", question_count=3, request_id=str(uuid4()), **kw)


def complete(client, db, learner, state):
    while state["current_question"]:
        question = state["current_question"]
        item = db.get(Attempt, question["attempt_id"])
        snapshot = item.question_snapshot
        answer = {"question_id": question["question_id"]}
        if question["question_type"] == "mcq": answer["selected_option_id"] = next(o["option_id"] for o in snapshot["options"] if o["is_correct"])
        elif question["question_type"] == "sql": answer["sql_answer"] = snapshot["reference_answer"]
        else: answer["essay_answer"] = snapshot["reference_answer"]
        response = client.post(f"/api/v1/sessions/{state['session_id']}/submit", headers=headers(learner), json=answer)
        assert response.status_code == 200, response.text
        assert response.json()["answer"]["score"] is None
        state = response.json()["state"]
    response = client.post(f"/api/v1/sessions/{state['session_id']}/finish", headers=headers(learner))
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("source", ["bank", "ai"])
def test_no_exam_and_frozen_scope_idempotent(client, db_session, source):
    _, learner, concepts = fixture(db_session)
    payload = selection(concepts)
    payload.update(source=source, difficulties=["HARD"])
    first = client.post('/api/v1/practice/start', headers=headers(learner), json=payload)
    assert first.status_code == 200, first.text
    second = client.post('/api/v1/practice/start', headers=headers(learner), json=payload)
    assert second.json()["session_id"] == first.json()["session_id"]
    session = db_session.get(AssessmentSession, first.json()["session_id"])
    assert session.assessment_id is None and db_session.scalar(select(func.count()).select_from(Assessment)) == 0
    for item in session.config_snapshot["question_plan"]:
        assert item["difficulty_level"] in (4, 5)
        assert {c["concept_id"] for c in item["concepts"]} <= set(payload["concept_ids"])
        assert sum(o["is_correct"] for o in item["options"]) == 1
    payload["source"] = "bank" if source == "ai" else "ai"
    assert client.post('/api/v1/practice/start', headers=headers(learner), json=payload).status_code == 409


def test_bank_shortfall_is_explicit_and_scope_not_widened(client, db_session):
    _, learner, concepts = fixture(db_session)
    payload = selection(concepts[:1])
    payload.update(difficulties=["HARD"], question_count=5)
    result = client.post('/api/v1/practice/start', headers=headers(learner), json=payload)
    assert result.status_code == 422
    assert result.json()["error"]["code"] == "insufficient_question_pool"
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 0


def test_flow_one_waits_for_evaluation_then_releases_and_cache(client, db_session):
    _, learner, concepts = fixture(db_session)
    state = client.post('/api/v1/practice/start', headers=headers(learner), json=selection(concepts)).json()
    complete(client, db_session, learner, state)
    path = f"/api/v1/evaluations/attempts/{state['session_id']}"
    pending = client.get(path, headers=headers(learner)).json()
    assert pending["status"] == "pending" and pending["history"] == [] and pending["dimensions"] == {} and pending["result"] is None
    assert client.get(f"/api/v1/sessions/{state['session_id']}/evidence", headers=headers(learner)).status_code == 409
    assert evaluations.process_one(db_session, force_fallback=True)
    view = client.get(path, headers=headers(learner)).json()
    assert view["status"] == "ready" and view["result"]["evaluator_fallback"]
    assert len(view["result"]["evaluation"]["question_comments"]) == 3
    assert client.get(path, headers=headers(learner)).json()["input_hash"] == view["input_hash"]
    assert not evaluations.process_one(db_session)
    assert client.get(f"/api/v1/sessions/{state['session_id']}/evidence", headers=headers(learner)).status_code == 200


def test_flow_two_sql_edit_reason_audit_and_approve(client, db_session):
    admin, learner, concepts = fixture(db_session)
    update_flow(db_session, "HUMAN_VERIFIED", admin)
    state = client.post('/api/v1/practice/start', headers=headers(learner), json=selection(concepts)).json()
    complete(client, db_session, learner, state)
    evaluations.process_one(db_session, force_fallback=True)
    sid = state["session_id"]
    path = f"/api/v1/evaluations/attempts/{sid}"
    assert client.get(path, headers=headers(learner)).json() == {"status": "awaiting_approval", "message": "Đang chờ giảng viên duyệt"}
    summary = client.get('/api/v1/sessions/statistics', headers=headers(learner)).json()
    assert summary["published_formal_sessions"] == 0
    review_path = f"/api/v1/admin/grading-reviews/{sid}"
    detail = client.get(review_path, headers=headers(admin)).json()
    assert detail["evaluation"]
    sql = next(i for i in detail["items"] if i["question_type"] == "sql")
    run = client.post(review_path+'/run-sql', headers=headers(admin), json={"question_id": sql["question_id"], "sql": "SELECT 1"})
    assert run.status_code == 200 and run.json()["success"]
    denied = client.post(review_path+'/run-sql', headers=headers(admin), json={"question_id": sql["question_id"], "sql": "DELETE FROM t"})
    assert denied.status_code == 200 and not denied.json()["success"]
    item = detail["items"][0]
    edit_path = review_path+f"/attempts/{item['attempt_id']}"
    assert client.post(edit_path, headers=headers(admin), json={"revision": 0, "score": "0"}).status_code == 422
    edited = client.post(edit_path, headers=headers(admin), json={"revision": 0, "score": "0", "comments": "Điều chỉnh theo rubric"})
    assert edited.status_code == 200, edited.text
    assert client.post(edit_path, headers=headers(admin), json={"revision": 0, "score": "0", "comments": "Điểm cũ"}).status_code == 409
    audit = db_session.scalar(select(GradeEditAudit))
    assert audit.reviewer_id == admin.account_id and audit.new_score == Decimal(0) and audit.old_score == Decimal(1)
    assert audit.reason and audit.created_at
    evaluations.process_one(db_session, force_fallback=True)
    detail = client.get(review_path, headers=headers(admin)).json()
    approved = client.post(review_path+'/publish', headers=headers(admin), json={"revision": detail["revision"]})
    assert approved.status_code == 200, approved.text
    view = client.get(path, headers=headers(learner)).json()
    assert view["status"] == "ready" and view["approved"] and view["adjusted"]
    assert client.get('/api/v1/sessions/statistics', headers=headers(learner)).json()["published_formal_sessions"] == 1


@pytest.mark.parametrize("count", [0, 1, 3])
def test_overall_adapts_to_history_size(client, db_session, count):
    _, learner, concepts = fixture(db_session)
    for _ in range(count):
        state = client.post('/api/v1/practice/start', headers=headers(learner), json=selection(concepts)).json()
        complete(client, db_session, learner, state)
        evaluations.process_one(db_session, force_fallback=True)
    result = client.get('/api/v1/evaluations/overall', headers=headers(learner)).json()
    assert result["attempt_count"] == count
    if not count: assert result["status"] == "empty"
    else:
        evaluations.process_one(db_session, force_fallback=True)
        result = client.get('/api/v1/evaluations/overall', headers=headers(learner)).json()
        assert (result["result"]["evaluation"]["trend"] is None) == (count == 1)
        assert len(result["history"]) == count


@pytest.mark.parametrize("mutation", [
    lambda q: q.update(concept_ids=[9999]), lambda q: q.update(difficulty_level=5),
    lambda q: q["options"][1].update(correct=True), lambda q: q.update(reference_answer=""),
    lambda q: q.update(unknown=True), lambda q: q.update(question_type="delete"),
])
def test_generated_scope_and_schema_are_strict(db_session, sandbox_runner, mutation):
    _, _, concepts = fixture(db_session)
    payload = practice.PracticeStart(**{**selection(concepts), "question_count": 1, "difficulties": ["EASY"]})
    raw = {"questions": practice.template_questions(concepts, payload)}
    assert practice.validate_generated(raw, concepts, payload, sandbox_runner)
    invalid = deepcopy(raw)
    mutation(invalid["questions"][0])
    with pytest.raises(ValueError): practice.validate_generated(invalid, concepts, payload, sandbox_runner)


def test_finishing_early_counts_every_planned_question_in_the_denominator(client, db_session):
    _, learner, concepts = fixture(db_session)
    payload = selection(concepts)
    payload.update(question_count=5, difficulties=["EASY"], source="ai")
    state = client.post('/api/v1/practice/start', headers=headers(learner), json=payload).json()
    question = state["current_question"]
    snap = db_session.get(Attempt, question["attempt_id"]).question_snapshot
    correct = next(o["option_id"] for o in snap["options"] if o["is_correct"])
    assert client.post(f"/api/v1/sessions/{state['session_id']}/submit", headers=headers(learner), json={"question_id": question["question_id"], "selected_option_id": correct}).status_code == 200
    assert client.post(f"/api/v1/sessions/{state['session_id']}/finish", headers=headers(learner)).status_code == 200
    evaluations.process_one(db_session, force_fallback=True)
    data, _ = evaluations.data_for(db_session, learner.account_id, state["session_id"])
    assert len(data["items"]) == 5 and data["history"][0]["percentage"] == 20


def test_generated_sql_checks_both_fixtures_and_stores_reproducible_snapshots(db_session, sandbox_runner):
    _, learner, concepts = fixture(db_session)
    payload = practice.PracticeStart(**{**selection(concepts[:1]), "question_count": 1, "source": "ai"})
    question = {"question_type": "sql", "concept_ids": payload.concept_ids, "difficulty_level": 2, "points": 1,
        "prompt": "Dùng SELECT để liệt kê id trong bảng t.", "reference_answer": "SELECT id FROM t",
        "setup_sql": "CREATE TABLE t(id int); INSERT INTO t VALUES (1),(2)", "edge_setup_sql": "CREATE TABLE t(id int)", "options": [], "rubrics": []}
    class Provider:
        def is_configured(self): return True
        def generate_structured(self, *args, **kw): return {"questions": [question]}
    state = practice.start(db_session, learner, payload, sandbox_runner, Provider())
    session = db_session.get(AssessmentSession, state.session_id)
    snap = session.config_snapshot["question_plan"][0]
    assert len(snap["datasets"]) == 2 and snap["datasets"][1]["is_edge_case"]
    assert snap["datasets"][0]["expected_result"]["rows"] == [[1], [2]]
    question["reference_answer"] = "SELECT missing FROM t"
    with pytest.raises(ValueError): practice.validate_generated({"questions": [question]}, concepts[:1], payload, sandbox_runner)


def test_admin_reset_revokes_old_credentials_and_enforces_role_boundary(client, db_session):
    admin, learner, _ = fixture(db_session)
    old = headers(learner)
    path = f"/api/v1/admin/accounts/{learner.account_id}/reset-password"
    assert client.post(path, headers=old, json={"password": "NewPassword123!"}).status_code == 403
    assert client.post(path, headers=headers(admin), json={"password": "short"}).status_code == 422
    assert client.post(path, headers=headers(admin), json={"password": "NewPassword123!"}).status_code == 200
    assert client.get('/api/v1/sessions', headers=old).status_code == 401
    assert client.post('/api/v1/auth/login', json={"email": learner.email, "password": "NewPassword123!"}).status_code == 200


def test_generated_attempt_questions_do_not_clutter_the_admin_bank(client, db_session):
    admin, learner, concepts = fixture(db_session)
    before = client.get('/api/v1/admin/questions', headers=headers(admin)).json()
    payload = selection(concepts)
    payload["source"] = "ai"
    state = client.post('/api/v1/practice/start', headers=headers(learner), json=payload)
    assert state.status_code == 200
    assert state.json()["question_source"] == "ai" and state.json()["generation_fallback"]
    assert client.get('/api/v1/admin/questions', headers=headers(admin)).json() == before
    assert len(db_session.get(AssessmentSession, state.json()["session_id"]).config_snapshot["question_plan"]) == 3


def test_ready_evaluation_and_release_are_read_as_one_consistent_state(client, db_session):
    _, learner, concepts = fixture(db_session)
    payload = selection(concepts)
    payload.update(source="ai", question_count=1)
    state = client.post('/api/v1/practice/start', headers=headers(learner), json=payload).json()
    complete(client, db_session, learner, state)
    row, data, _ = evaluations.ensure(db_session, learner.account_id, state["session_id"])
    from app.services.evaluation_pipeline import evaluate
    row.payload, row.status = evaluate(data, force_fallback=True), "ready"
    db_session.commit()
    view = client.get(f"/api/v1/evaluations/attempts/{state['session_id']}", headers=headers(learner)).json()
    assert view["status"] == "ready" and view["result"] and view["score"]
    assert view["history"] and view["dimensions"]


def test_late_worker_cannot_overwrite_an_evaluation_recovered_by_retry(client, db_session, monkeypatch):
    _, learner, concepts = fixture(db_session)
    payload = selection(concepts)
    payload.update(source="ai", question_count=1)
    state = client.post('/api/v1/practice/start', headers=headers(learner), json=payload).json()
    complete(client, db_session, learner, state)
    from app.db import get_session_factory
    from app.services.evaluation_pipeline import evaluate
    def finish_newer(data, *args, **kwargs):
        newer = evaluate(data, force_fallback=True)
        newer["evaluation"]["summary"] = "Newer completed evaluation"
        with get_session_factory()() as other:
            record = other.scalar(select(EvaluationRecord).where(EvaluationRecord.session_id == state["session_id"]))
            record.status, record.payload, record.lease_until = "ready", newer, None
            other.commit()
        stale = evaluate(data, force_fallback=True)
        stale["evaluation"]["summary"] = "Stale evaluation"
        return stale
    monkeypatch.setattr(evaluations, "evaluate", finish_newer)
    assert evaluations.process_one(db_session)
    db_session.expire_all()
    record = db_session.scalar(select(EvaluationRecord).where(EvaluationRecord.session_id == state["session_id"]))
    assert record.status == "ready" and record.payload["evaluation"]["summary"] == "Newer completed evaluation"
