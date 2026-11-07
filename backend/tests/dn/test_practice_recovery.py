"""All required deterministic provider failures through real API/DB/sandbox."""
from copy import deepcopy
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import func, select

from app.deps import get_llm_service
from app.main import app
from app.models import AssessmentSession, Question
from app.services.corpus_seed import sync_bank
from app.services.practice_bank import content_errors
from app.services.practice_generation import ai_type_targets, template_questions
from app.services.practice_selection import Candidate, Catalog, complete_batch, recovered_plan
from app.services.practice_service import PracticeStart
from app.validate_bank import load_corpus
from test_ai_admin import _make_account
from test_supervisor_requirements import headers


@pytest.mark.parametrize("mode", ["schema", "provider"])
def test_generation_diagnostics_never_log_provider_or_question_content(caplog, mode):
    from types import SimpleNamespace
    from app.services.practice_generation import generate_entries
    concept = SimpleNamespace(concept_id=1, concept_code="SQL-SELECT", concept_name="SELECT", description="Projection")
    payload = PracticeStart(concept_ids=[1], difficulties=["EASY"], source="ai", question_count=1, request_id=uuid4())
    class Provider:
        def is_configured(self): return True
        def generate_structured(self, *args, **kwargs):
            if mode == "provider": raise RuntimeError("private credential and response")
            return {"questions": [{"prompt": "private question content"}]}
    assert generate_entries([concept], payload, SimpleNamespace(account_id=1), None, Provider()) == []
    assert caplog.text.count("Practice generation rejected") == 2
    assert "reason=" + ("generation_schema" if mode == "schema" else "provider_or_validation") in caplog.text
    assert "private" not in caplog.text


def valid_bank(db):
    admin = _make_account(db, "recovery-admin@test.dev", "Administrator")
    learner = _make_account(db, "recovery-learner@test.dev", "Learner")
    packs, _ = load_corpus()
    concept = next(c for p in packs for c in p["concepts"] if c["concept_code"] == "SQL-SELECT")
    pack = {"concepts": [concept], "clos": [], "dependencies": {}, "assessments": [],
            "questions": [q for q in packs[-1]["questions"] if q["concept_codes"] == ["SQL-SELECT"]]}
    sync_bank(db, admin, packs=[pack]); db.commit()
    from app.models import Concept
    c = db.scalar(select(Concept).where(Concept.concept_code == "SQL-SELECT"))
    return admin, learner, [c]


def ai_wire(concepts, payload):
    targets = ai_type_targets(payload.question_count)
    count = sum(targets.values())
    return template_questions(concepts, payload.model_copy(update={"question_count": count}),
                              kinds=tuple(targets), type_targets_override=targets)


@pytest.mark.parametrize("mode,expected_code", [
    ("normal", None), ("provider_failure", "provider_or_validation"), ("invalid_schema", "schema"),
    ("multiple_correct", "mcq_options"), ("provider_sql", "type_source"), ("invalid_sql", "type_source"),
    ("empty_sql", "type_source"), ("empty_sql_edge", "type_source"), ("environment_sql", "type_source"),
    ("duplicates", "duplicate"), ("wrong_concept", "out_of_scope_concept"),
    ("wrong_difficulty", "difficulty_mismatch"), ("timeout", "timeout"), ("partial", None),
    ("retry_exhaustion", "schema"), ("empty", "count"),
])
def test_every_generation_failure_preserves_exact_count_and_valid_content(
        client, db_session, sandbox_runner, monkeypatch, mode, expected_code):
    _, learner, concepts = valid_bank(db_session)
    payload = PracticeStart(concept_ids=[concepts[0].concept_id], difficulties=["EASY"], source="ai",
                            question_count=3, request_id=uuid4())
    wire = ai_wire(concepts, payload)
    sql_sample = next(q for q in template_questions(concepts, payload) if q["question_type"] == "sql")
    class Provider:
        calls = 0
        def is_configured(self): return True
        def generate_structured(self, *args, **kwargs):
            self.calls += 1
            if mode == "provider_failure": raise RuntimeError("deterministic failure")
            if mode == "timeout": raise httpx.ReadTimeout("deterministic timeout")
            if mode in ("invalid_schema", "retry_exhaustion"):
                return {"questions": [{"prompt": "private malformed question content"}]}
            if mode == "empty": return {"questions": []}
            batch = deepcopy(wire)
            if mode == "multiple_correct": next(o for o in batch[0]["options"] if not o["correct"])["correct"] = True
            if mode in ("provider_sql", "invalid_sql", "empty_sql", "empty_sql_edge", "environment_sql"):
                batch[0] = deepcopy(sql_sample)
                if mode == "invalid_sql": batch[0]["reference_answer"] = "SELECT missing FROM cases"
                if mode == "environment_sql": batch[0]["reference_answer"] = "SELECT current_schema()"
                if mode == "empty_sql": batch[0]["reference_answer"] = "SELECT id FROM cases WHERE false"
                if mode == "empty_sql_edge":
                    batch[0]["edge_setup_sql"] = batch[0]["edge_setup_sql"].split("INSERT INTO")[0]
            if mode == "duplicates": batch[1] = deepcopy(batch[0])
            if mode == "wrong_concept": batch[0]["concept_ids"] = [999999]
            if mode == "wrong_difficulty": batch[0]["difficulty_level"] = 5
            if mode == "partial": batch = batch[:1]
            return {"questions": batch}
    provider = Provider()
    monkeypatch.setitem(app.dependency_overrides, get_llm_service, lambda: provider)
    response = client.post('/api/v1/practice/start', headers=headers(learner), json=payload.model_dump(mode="json"))
    assert response.status_code == 200, response.text
    session = db_session.get(AssessmentSession, response.json()["session_id"])
    snapshot = session.config_snapshot
    ids = snapshot["question_ids"]
    assert len(ids) == len(set(ids)) == 3
    assert len({q["prompt"] for q in snapshot["question_plan"]}) == 3
    assert all(not content_errors(db_session.get(Question, qid)) for qid in ids)
    assert provider.calls == (1 if mode == "normal" else 2)
    assert response.json()["generation_fallback"] is True
    assert response.json()["bank_mixed"] is True and response.json()["template_fallback"] is False
    assert response.json()["selection_notice"]
    origins = {(p["origin"], q["question_type"])
               for p, q in zip(snapshot["selection_provenance"], snapshot["question_plan"])}
    assert all(origin == "bank" for origin, kind in origins if kind == "sql")
    if mode == "normal":
        assert response.json()["ai_generated_count"] == 2
        assert {kind for origin, kind in origins if origin == "ai"} == {"mcq", "essay"}
        assert not snapshot["generation_diagnostics"]
    else:
        assert response.json()["ai_generated_count"] == (1 if mode == "partial" else 0)
        if expected_code:
            assert any(d["code"] == expected_code for d in snapshot["generation_diagnostics"]), \
                snapshot["generation_diagnostics"]
    replay = client.post('/api/v1/practice/start', headers=headers(learner), json=payload.model_dump(mode="json"))
    replayed, original = replay.json(), response.json()
    assert replayed.pop("server_now") >= original.pop("server_now")
    assert replayed == original
    assert provider.calls == (1 if mode == "normal" else 2)
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 1


@pytest.mark.parametrize("shape", ["list", "items", "data", "result", "nested"])
def test_reasonable_root_variants_are_normalized_before_strict_validation(db_session, shape):
    from app.services.practice_generation import generate_entries
    _, learner, concepts = valid_bank(db_session)
    payload = PracticeStart(concept_ids=[concepts[0].concept_id], difficulties=["EASY"], source="ai",
                            question_count=3, request_id=uuid4())
    wire = ai_wire(concepts, payload)
    roots = {"list": wire, "items": {"items": wire}, "data": {"data": wire},
             "result": {"result": {"questions": wire}}, "nested": {"items": {"questions": wire}}}
    class Provider:
        def is_configured(self): return True
        def generate_structured(self, *args, **kwargs): return roots[shape]
    diagnostics = []
    entries = generate_entries(concepts, payload, learner, None, Provider(), diagnostics=diagnostics)
    assert [item["question_type"] for item in entries] == ["mcq", "essay"]
    assert diagnostics == []


def test_malformed_root_reports_count_without_leaking_raw_response():
    from types import SimpleNamespace
    from app.services.practice_generation import generate_entries
    concept = SimpleNamespace(concept_id=1, concept_code="SQL-SELECT", concept_name="SELECT", description="Projection")
    payload = PracticeStart(concept_ids=[1], difficulties=["EASY"], source="ai", question_count=1, request_id=uuid4())
    class Provider:
        def is_configured(self): return True
        def generate_structured(self, *args, **kwargs):
            return {"items": "private provider content"}
    diagnostics = []
    assert generate_entries([concept], payload, SimpleNamespace(account_id=1), None, Provider(),
                            diagnostics=diagnostics) == []
    assert [entry["code"] for entry in diagnostics] == ["count", "count"]
    assert all("private" not in str(entry) for entry in diagnostics)


def test_repeated_partial_batches_are_deduplicated_before_serving(db_session):
    from app.services.practice_generation import generate_entries
    _, learner, concepts = valid_bank(db_session)
    payload = PracticeStart(concept_ids=[concepts[0].concept_id], difficulties=["EASY"], source="ai",
                            question_count=3, request_id=uuid4())
    partial = ai_wire(concepts, payload)[:1]
    class Provider:
        def is_configured(self): return True
        def generate_structured(self, *args, **kwargs): return {"questions": deepcopy(partial)}
    diagnostics = []
    entries = generate_entries(concepts, payload, learner, None, Provider(), diagnostics=diagnostics)
    assert len(entries) == 1
    assert [entry["code"] for entry in diagnostics] == ["count", "count"]


def test_repeated_partial_batches_cannot_bypass_duplicate_or_balance_checks():
    one = Candidate("first", "mcq", 2, frozenset({1}), "first", "same prompt", {})
    ai = [replace(one, origin="ai"), replace(one, identity="second", family="second", origin="ai")]
    bank = Catalog([Candidate(str(i), kind, 2, frozenset({1}), str(i), str(i), {})
                    for i, kind in enumerate(("mcq", "sql", "essay"))]).prepare({1}, {"EASY"})
    assert not complete_batch(ai, 2, {1}, {"EASY"})
    assert recovered_plan(bank, ai, 2, {1}, {"EASY"}).take(2) == bank.take(2)


@pytest.mark.parametrize("blank", ["llm_api_key", "llm_base_url", "llm_model"])
def test_whitespace_provider_configuration_cannot_send_a_request(blank):
    from app.config import Settings
    from app.services.llm import LLMService
    from app.services.llm.errors import LLMError
    settings = Settings(_env_file=None, deployment_mode="development", llm_api_key="fixture-key",
                        llm_base_url="https://provider.test/v1", llm_model="fixture-model")
    service = LLMService(settings.model_copy(update={blank: " \t "}))
    assert not service.is_configured()
    with pytest.raises(LLMError):
        service.generate_structured("practice_generation", [])


def test_budget_applies_to_initialized_client_and_preserves_fake_transport():
    from app.config import Settings
    from app.services.llm import LLMService
    from app.services.llm.provider import ChatCompletionsProvider, ChatMessage
    from app.services.llm.errors import LLMError
    calls = []
    def timeout(request):
        calls.append(request.extensions["timeout"]["read"])
        raise httpx.ReadTimeout("deterministic timeout")
    provider = ChatCompletionsProvider("https://provider.test/v1", "fixture-key", timeout_seconds=120,
        max_retries=2, transport=httpx.MockTransport(timeout))
    service = LLMService(Settings(_env_file=None, deployment_mode="development", llm_api_key="fixture-key",
        llm_base_url="https://provider.test/v1", llm_model="fixture-model", llm_timeout_seconds=120), provider=provider)
    assert service._get_provider() is provider
    with pytest.raises(LLMError):
        service.with_budget(timeout_seconds=.25, max_retries=0).generate_structured("fixture", [ChatMessage("user", "Return JSON")])
    assert calls == [.25]


def test_full_size_fake_generation_uses_verified_grids_and_serves_twenty_ai_questions(client, db_session, monkeypatch):
    _, learner, concepts = valid_bank(db_session)
    payload = PracticeStart(concept_ids=[concepts[0].concept_id], source="ai", question_count=20, request_id=uuid4())
    wire = ai_wire(concepts, payload)
    class Provider:
        calls = 0
        def is_configured(self): return True
        def generate_structured(self, *args, **kwargs):
            self.calls += 1
            return {"questions": wire}
    provider = Provider()
    monkeypatch.setitem(app.dependency_overrides, get_llm_service, lambda: provider)
    response = client.post('/api/v1/practice/start', headers=headers(learner), json=payload.model_dump(mode="json"))
    assert response.status_code == 200, response.text
    assert response.json()["max_questions"] == 20
    session = db_session.get(AssessmentSession, response.json()["session_id"])
    snapshot = session.config_snapshot
    assert response.json()["generation_fallback"] is True and response.json()["bank_mixed"] is True
    assert response.json()["template_fallback"] is False and response.json()["ai_generated_count"] == 13
    assert len(set(snapshot["question_ids"])) == 20
    assert len({q["prompt"] for q in snapshot["question_plan"]}) == 20
    origins = {(p["origin"], q["question_type"])
               for p, q in zip(snapshot["selection_provenance"], snapshot["question_plan"])}
    assert {kind for origin, kind in origins if origin == "ai"} == {"mcq", "essay"}
    assert {kind for origin, kind in origins if origin == "bank"} == {"sql"}
    assert provider.calls == 1
