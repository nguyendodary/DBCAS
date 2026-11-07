"""New practice contracts against PostgreSQL and the real SELECT sandbox."""
from copy import deepcopy
from uuid import uuid4
from decimal import Decimal
import pytest
from sqlalchemy import select, func

from app.models import Assessment, AssessmentSession, Attempt, GradeEditAudit, EvaluationRecord
from app.errors import AppError
from app.services import evaluation_service as evaluations, practice_service as practice
from app.services.system_settings import update_flow
from test_adaptive_engine import _make_account, _concept, _mcq, _sql, _essay
from test_supervisor_requirements import headers


def fixture(db):
    from app.schemas import QuestionUpsertRequest
    from app.services.question_service import create_question
    from app.services.practice_corpus import template_pack
    from app.models import Question
    admin = _make_account(db, "practice-admin@test.dev", "Administrator")
    learner = _make_account(db, "practice-learner@test.dev", "Learner")
    concepts = [_concept(db, code) for code in ("SQL-SELECT", "SQL-WHERE")]
    def create(concept, kind, level, variant):
        band = "easy" if level <= 2 else "medium" if level == 3 else "hard"
        key = f"case-{concept.concept_code.lower()}-{band}-{variant}-{kind}"
        q = deepcopy(next(q for q in template_pack()["questions"] if q["key"] == key))
        q.update(concept_ids=[concept.concept_id], difficulty_level=level, points=1)
        if kind == "essay":
            for row, lo, hi in zip(q["rubrics"], (0, .25, .5, .75), (.24, .49, .74, 1)):
                row.update(min_score=lo, max_score=hi)
        created = create_question(db, QuestionUpsertRequest(**q), admin)
        db.get(Question, created.question_id).status = "validated"
    for concept in concepts:
        for level in range(1, 6): create(concept, "mcq", level, level)
    create(concepts[0], "sql", 2, 1)
    create(concepts[0], "essay", 3, 1)
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


def test_bank_shortfall_widens_deterministically_to_exact_count_and_discloses(client, db_session):
    _, learner, concepts = fixture(db_session)
    payload = selection(concepts[:1])
    payload.update(difficulties=["HARD"], question_count=5)
    result = client.post('/api/v1/practice/start', headers=headers(learner), json=payload)
    assert result.status_code == 200, result.text
    session = db_session.get(AssessmentSession, result.json()["session_id"])
    assert len(session.config_snapshot["question_plan"]) == 5
    assert result.json()["selection_notice"]
    assert any(p["tier"] == 1 for p in session.config_snapshot["selection_provenance"])
    replay = client.post('/api/v1/practice/start', headers=headers(learner), json=payload)
    replayed, original = replay.json(), result.json()
    assert replayed.pop("server_now") >= original.pop("server_now")
    assert replayed == original
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 1


@pytest.mark.parametrize("configured", [False, True])
def test_ai_failure_with_insufficient_bank_uses_verified_templates_at_exact_count(client, db_session, configured, monkeypatch):
    _, learner, concepts = fixture(db_session)
    payload = practice.PracticeStart(**{**selection(concepts[:1]), "source": "ai", "difficulties": ["HARD"], "question_count": 20})

    class FailedProvider:
        calls = 0
        def is_configured(self): return True
        def generate_structured(self, *args, **kwargs):
            self.calls += 1
            raise RuntimeError("provider unavailable")

    provider = FailedProvider() if configured else None
    started = practice.start(db_session, learner, payload, llm=provider)
    session = db_session.get(AssessmentSession, started.session_id)
    assert len(session.config_snapshot["question_plan"]) == 20
    assert len(set(session.config_snapshot["question_ids"])) == 20 and started.generation_fallback
    assert any(p["origin"] == "template" for p in session.config_snapshot["selection_provenance"])
    from app.services.practice_bank import content_errors
    from app.models import Question
    assert all(not content_errors(db_session.get(Question, qid)) for qid in session.config_snapshot["question_ids"])
    if provider: assert provider.calls == 2
    from app.deps import get_llm_service
    from app.main import app
    monkeypatch.setitem(app.dependency_overrides, get_llm_service, lambda: FailedProvider() if configured else None)
    response = client.post('/api/v1/practice/start', headers=headers(learner), json=payload.model_dump(mode="json"))
    assert response.status_code == 200 and response.json()["session_id"] == started.session_id
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 1


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
    lambda q: q.update(question_type="MCQ"),
])
def test_generated_scope_and_schema_are_strict(db_session, sandbox_runner, mutation):
    _, _, concepts = fixture(db_session)
    payload = practice.PracticeStart(**{**selection(concepts), "question_count": 1, "difficulties": ["EASY"]})
    raw = {"questions": practice.template_questions(concepts, payload)}
    assert practice.validate_generated(raw, concepts, payload, sandbox_runner)
    invalid = deepcopy(raw)
    mutation(invalid["questions"][0])
    with pytest.raises(ValueError): practice.validate_generated(invalid, concepts, payload, sandbox_runner)


def test_generation_schema_tells_provider_the_accepted_question_types():
    schema = practice.GeneratedQuestion.model_json_schema()
    assert schema["properties"]["question_type"]["enum"] == ["mcq", "sql", "essay"]


@pytest.mark.parametrize("kind", ["mcq", "essay"])
@pytest.mark.parametrize("field", ["setup_sql", "edge_setup_sql"])
def test_non_sql_generation_does_not_silently_discard_sql_fixtures(kind, field):
    from types import SimpleNamespace
    concept = SimpleNamespace(concept_id=7, concept_name="SELECT", description="Retrieve selected columns.")
    payload = practice.PracticeStart(concept_ids=[7], difficulties=["EASY"], source="ai",
                                     question_count=1, request_id=uuid4())
    question = practice.template_questions([concept], payload)[0]
    question["question_type"] = kind
    if kind == "essay":
        question.update(points=4, options=[], reference_answer="SELECT lấy các cột đầu ra; cần giải thích đầy đủ dữ liệu và giá trị NULL.", rubrics=[
            dict(level_name=level, min_score=minimum, max_score=maximum, criteria="Giải thích quy tắc và kết quả theo các bằng chứng được yêu cầu.")
            for level, minimum, maximum in (("Incomplete", 0.0, 0.99), ("Partial", 1.0, 1.99),
                ("Mostly Complete", 2.0, 2.99), ("Complete", 3.0, 4.0))])
    assert practice.validate_generated({"questions": [question]}, [concept], payload, None)
    question[field] = "CREATE TABLE t(id int PRIMARY KEY); INSERT INTO t VALUES (1),(1);"
    with pytest.raises(ValueError, match="generation_type_fields"):
        practice.validate_generated({"questions": [question]}, [concept], payload, None)


@pytest.mark.parametrize("bank_available", [True, False])
def test_wrong_type_fixtures_use_bank_or_fail_without_persisting_generated_questions(db_session, bank_available):
    from app.models import Question
    _, learner, concepts = fixture(db_session)
    payload = practice.PracticeStart(**{**selection(concepts[:1]), "source": "ai", "difficulties": ["HARD"],
                                       "question_count": 1 if bank_available else 3})
    generated = practice.template_questions(concepts[:1], payload)
    generated[0]["setup_sql"] = "CREATE TABLE t(id int PRIMARY KEY); INSERT INTO t VALUES (1),(1);"
    before = db_session.scalar(select(func.count()).select_from(Question))
    class Provider:
        calls = 0
        def is_configured(self): return True
        def generate_structured(self, *args, **kwargs):
            self.calls += 1
            return {"questions": generated}
    provider = Provider()
    state = practice.start(db_session, learner, payload, llm=provider)
    assert state.generation_fallback is True
    assert len(db_session.get(AssessmentSession, state.session_id).config_snapshot["question_plan"]) == payload.question_count
    assert provider.calls == 2
    assert db_session.scalar(select(func.count()).select_from(Question)) == before


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


def ai_wire(concepts, payload):
    """Deterministic non-SQL provider batch matching the bank-SQL contract."""
    targets = practice.ai_type_targets(payload.question_count)
    count = sum(targets.values())
    return practice.template_questions(
        concepts, payload.model_copy(update={"question_count": count}),
        kinds=tuple(targets), type_targets_override=targets)


def test_generated_sql_checks_both_fixtures_and_stores_reproducible_snapshots(db_session, sandbox_runner):
    _, learner, concepts = fixture(db_session)
    payload = practice.PracticeStart(**{**selection(concepts[:1]), "question_count": 1, "source": "ai"})
    question = {"question_type": "sql", "concept_ids": payload.concept_ids, "difficulty_level": 2, "points": 1,
        "prompt": "Dùng SELECT để liệt kê id trong bảng t.", "reference_answer": "SELECT id FROM t",
        "explanation": "SELECT id trả toàn bộ mã trong bảng t, không lọc hoặc loại trùng.",
        "source_refs": ["https://www.postgresql.org/docs/18/queries-select-lists.html"],
        "setup_sql": "CREATE TABLE t(id int); INSERT INTO t VALUES (1),(2)", "edge_setup_sql": "CREATE TABLE t(id int); INSERT INTO t VALUES (NULL),(3)", "options": [], "rubrics": []}
    validated = practice.validate_generated({"questions": [question]}, concepts[:1], payload, sandbox_runner)
    datasets = validated[0]["_datasets"]
    assert len(datasets) == 2 and datasets[1]["is_edge_case"]
    assert datasets[0]["expected_result"]["rows"] == [[1], [2]]
    assert datasets[1]["expected_result"]["rows"] == [[None], [3]]
    question["reference_answer"] = "SELECT missing FROM t"
    with pytest.raises(ValueError): practice.validate_generated({"questions": [question]}, concepts[:1], payload, sandbox_runner)

    mixed = payload.model_copy(update={"question_count": 3})
    class Provider:
        def is_configured(self): return True
        def generate_structured(self, *args, **kw): return {"questions": ai_wire(concepts[:1], mixed)}
    state = practice.start(db_session, learner, mixed, sandbox_runner, Provider())
    session = db_session.get(AssessmentSession, state.session_id)
    sql_snap = next(s for s in session.config_snapshot["question_plan"] if s["question_type"] == "sql")
    assert len(sql_snap["datasets"]) == 2 and sql_snap["datasets"][1]["is_edge_case"]
    assert sql_snap["datasets"][0]["expected_result"]["rows"]
    assert session.config_snapshot["selection_provenance"][
        next(i for i, s in enumerate(session.config_snapshot["question_plan"]) if s["question_type"] == "sql")
    ]["origin"] == "bank"


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


def test_live_generation_reuses_retries_but_not_a_different_attempt(client, db_session):
    import json
    from app.config import Settings
    from app.services.llm import LLMService
    _, learner, concepts = fixture(db_session)
    first = practice.PracticeStart(**{**selection(concepts[:1]), "source": "ai", "question_count": 1})
    class Cache:
        def __init__(self): self.values = {}
        def find(self, key): return self.values.get(key)
        def store(self, key, task, model, result): self.values[key] = result
    class Provider:
        calls = 0
        def generate(self, request):
            self.calls += 1
            questions = practice.template_questions(concepts[:1], first)
            questions[0]["prompt"] += f" Batch {self.calls}."
            return json.dumps({"questions": questions})
    provider = Provider()
    service = LLMService(Settings(llm_api_key="test", llm_base_url="http://fake.invalid/v1", llm_model="fake"),
                         provider=provider, cache=Cache())
    started = practice.start(db_session, learner, first, None, service)
    replayed = practice.start(db_session, learner, first, None, service)
    assert provider.calls == 1 and replayed.session_id == started.session_id
    complete(client, db_session, learner, started.model_dump(mode="json"))
    second = first.model_copy(update={"request_id": uuid4()})
    fresh = practice.start(db_session, learner, second, None, service)
    assert provider.calls == 2 and fresh.session_id != started.session_id
    assert fresh.current_question.prompt != started.current_question.prompt


def test_invalid_domain_response_is_not_cached_and_bounded_retry_recovers(db_session, sandbox_runner):
    import json
    from app.config import Settings
    from app.models import Question
    from app.services.llm import LLMService
    _, learner, concepts = fixture(db_session)
    payload = practice.PracticeStart(**{**selection(concepts[:1]), "source": "ai", "difficulties": ["HARD"]})
    questions = ai_wire(concepts[:1], payload)
    class Cache:
        values = {}
        def find(self, key): return self.values.get(key)
        def store(self, key, task, model, response): self.values[key] = response
    class Provider:
        calls = 0
        def generate(self, request):
            self.calls += 1
            assert not cache.values
            assert db_session.scalar(select(func.count()).select_from(Question)) == before
            batch = deepcopy(questions)
            if self.calls == 1:
                batch[0]["setup_sql"] = "CREATE TABLE t(id int PRIMARY KEY); INSERT INTO t VALUES (1),(1);"
            return json.dumps({"questions": batch})
    cache, provider = Cache(), Provider()
    service = LLMService(Settings(_env_file=None, deployment_mode="development", llm_api_key="fake-test-key",
        llm_base_url="https://provider.test/v1", llm_model="fake-test-model"), provider=provider, cache=cache)
    before = db_session.scalar(select(func.count()).select_from(Question))
    recovered = practice.start(db_session, learner, payload, sandbox_runner, service)
    assert recovered.generation_fallback is True and recovered.bank_mixed is True
    assert recovered.template_fallback is False and recovered.ai_generated_count == 2
    snapshot = db_session.get(AssessmentSession, recovered.session_id).config_snapshot
    assert any(d["code"] == "type_fields" for d in snapshot["generation_diagnostics"])
    origins = {(p["origin"], q["question_type"])
               for p, q in zip(snapshot["selection_provenance"], snapshot["question_plan"])}
    assert ("bank", "sql") in origins and ("ai", "mcq") in origins and ("ai", "essay") in origins
    assert provider.calls == 2 and len(cache.values) == 1
    assert db_session.scalar(select(func.count()).select_from(Question)) == before + 2
    replay = practice.start(db_session, learner, payload, llm=service)
    assert replay.session_id == recovered.session_id and provider.calls == 2


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
