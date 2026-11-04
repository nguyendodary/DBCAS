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
from app.services.practice_generation import template_questions
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


@pytest.mark.parametrize("mode", ["normal", "provider_failure", "invalid_schema", "multiple_correct", "invalid_sql",
    "empty_sql", "empty_sql_edge", "environment_sql", "duplicates", "wrong_concept", "wrong_difficulty", "timeout", "partial", "retry_exhaustion"])
def test_every_generation_failure_preserves_exact_count_and_valid_content(client, db_session, sandbox_runner, monkeypatch, mode):
    _, learner, concepts = valid_bank(db_session)
    payload = PracticeStart(concept_ids=[concepts[0].concept_id], difficulties=["EASY"], source="ai", question_count=3, request_id=uuid4())
    wire = template_questions(concepts, payload)
    class Provider:
        calls = 0
        def is_configured(self): return True
        def generate_structured(self, *args, **kwargs):
            self.calls += 1
            if mode == "provider_failure": raise RuntimeError("deterministic failure")
            if mode == "timeout": raise httpx.ReadTimeout("deterministic timeout")
            if mode in ("invalid_schema", "retry_exhaustion"): return {"unexpected": []}
            batch = deepcopy(wire)
            if mode == "multiple_correct": next(o for o in batch[0]["options"] if not o["correct"])["correct"] = True
            if mode == "invalid_sql": next(q for q in batch if q["question_type"] == "sql")["reference_answer"] = "SELECT missing FROM cases"
            if mode == "environment_sql": next(q for q in batch if q["question_type"] == "sql")["reference_answer"] = "SELECT current_schema()"
            if mode == "empty_sql": next(q for q in batch if q["question_type"] == "sql")["reference_answer"] = "SELECT id FROM cases WHERE false"
            if mode == "empty_sql_edge":
                sql = next(q for q in batch if q["question_type"] == "sql")
                sql["edge_setup_sql"] = sql["edge_setup_sql"].split("INSERT INTO")[0]
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
    ids = session.config_snapshot["question_ids"]
    assert len(ids) == len(set(ids)) == 3
    assert len({q["prompt"] for q in session.config_snapshot["question_plan"]}) == 3
    assert all(not content_errors(db_session.get(Question, qid)) for qid in ids)
    assert provider.calls == (1 if mode == "normal" else 2)
    if mode != "normal": assert response.json()["generation_fallback"] and response.json()["selection_notice"]
    replay = client.post('/api/v1/practice/start', headers=headers(learner), json=payload.model_dump(mode="json"))
    replayed, original = replay.json(), response.json()
    assert replayed.pop("server_now") >= original.pop("server_now")
    assert replayed == original
    assert provider.calls == (1 if mode == "normal" else 2)
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 1


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
    wire = template_questions(concepts, payload)
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
    assert response.json()["max_questions"] == 20 and response.json()["generation_fallback"] is False
    session = db_session.get(AssessmentSession, response.json()["session_id"])
    assert len(set(session.config_snapshot["question_ids"])) == 20
    assert all(p["origin"] == "ai" for p in session.config_snapshot["selection_provenance"])
    assert provider.calls == 1
