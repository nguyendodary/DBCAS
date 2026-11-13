"""The Evaluator must receive the exact built prompt, with a matching hash."""
import hashlib
import json
import logging

import httpx
import pytest

from app.config import Settings
from app.services.evaluation_pipeline import evaluate, rule_evaluation, sanitize_data
from app.services.llm import ChatCompletionsProvider, LLMService
from app.services.prompt_builder import build_prompt

DATA = {
    "version": "two-ai-v4",
    "mode": "attempt",
    "attempt_count": 1,
    "score": {"earned": "1", "possible": "2", "percentage": 50.0},
    "history": [{"session_id": 7, "ordinal": 1, "date": "2026-11-10T00:00:00+00:00",
                 "earned": "1", "possible": "2", "percentage": 50.0}],
    "dimensions": {},
    "items": [
        {"attempt_id": 201, "question_id": 21, "type": "mcq", "points": "1", "score": "1", "answer": "candidate key"},
        {"attempt_id": 202, "question_id": 22, "type": "essay", "points": "2", "score": None,
         "answer": "Email learner.private@example.edu or call 090-123-4567 about lossless joins.",
         "reference_answer": "A lossless join restores exactly the original rows."},
    ],
}

PII = "learner.private@example.edu"
PHONE = "090-123-4567"


class DictCache:
    def __init__(self):
        self.data = {}
        self.stores = 0

    def find(self, request_hash):
        return self.data.get(request_hash)

    def store(self, request_hash, task_type, model, response):
        self.data[request_hash] = response
        self.stores += 1


class CaptureLLM:
    def __init__(self):
        self.messages = None
        self.kwargs = None

    def is_configured(self):
        return True

    def generate_structured(self, task_type, messages, **kwargs):
        self.messages = messages
        self.kwargs = kwargs
        payload = rule_evaluation(sanitize_data(DATA))
        return kwargs["validator"](payload)


def _settings(**over):
    values = {
        "llm_api_key": "test-key",
        "llm_base_url": "https://provider.test/v1",
        "llm_model": "test-model",
        "llm_backoff_seconds": 0.0,
        "llm_max_retries": 1,
        "llm_timeout_seconds": 10,
    }
    values.update(over)
    return Settings(_env_file=None, **values)


def _provider(handler, *, max_retries=0):
    return ChatCompletionsProvider(
        "https://provider.test/v1", "test-key", transport=httpx.MockTransport(handler),
        max_retries=max_retries, backoff_seconds=0.0, sleeper=lambda _: None)


def _completion(payload):
    return {"choices": [{"message": {"content": json.dumps(payload)}}]}


def _evaluation_from_prompt(content):
    data = json.loads(content.split("## DỮ LIỆU\n", 1)[1].split("## KHÁI NIỆM\n", 1)[0])
    return rule_evaluation(data)


def test_evaluator_receives_the_exact_built_prompt_and_matching_hash():
    capture = CaptureLLM()
    result = evaluate(DATA, capture)
    assert not result["evaluator_fallback"]
    assert capture.kwargs["sanitize_messages"] is False
    user_prompt = capture.messages[-1].content
    assert user_prompt == build_prompt(sanitize_data(DATA)).prompt
    assert hashlib.sha256(user_prompt.encode()).hexdigest() == result["prompt_hash"]
    assert PII not in user_prompt and PHONE not in user_prompt
    assert "[id]" in user_prompt


def test_evaluator_receives_the_model_builder_prompt_not_a_rebuilt_one(monkeypatch):
    from types import SimpleNamespace
    from app.services import prompt_builder

    model_prompt = prompt_builder.template_prompt(sanitize_data(DATA))
    monkeypatch.setattr(prompt_builder, "local_inference", lambda *_: model_prompt)
    capture = CaptureLLM()
    settings = SimpleNamespace(prompt_builder_model_path="local", prompt_builder_timeout_seconds=8)
    result = evaluate(DATA, capture, settings=settings)
    assert not result["builder_fallback"] and not result["evaluator_fallback"]
    assert capture.messages[-1].content == model_prompt
    assert hashlib.sha256(model_prompt.encode()).hexdigest() == result["prompt_hash"]


def test_invalid_model_builder_falls_back_before_the_same_prompt_is_sent(monkeypatch):
    from types import SimpleNamespace
    from app.services import prompt_builder

    def broken(*_):
        raise TimeoutError("builder-secret-token")

    monkeypatch.setattr(prompt_builder, "local_inference", broken)
    capture = CaptureLLM()
    settings = SimpleNamespace(prompt_builder_model_path="local", prompt_builder_timeout_seconds=8)
    result = evaluate(DATA, capture, settings=settings)
    assert result["builder_fallback"] and not result["evaluator_fallback"]
    assert capture.messages[-1].content == build_prompt(sanitize_data(DATA)).prompt
    assert hashlib.sha256(capture.messages[-1].content.encode()).hexdigest() == result["prompt_hash"]


def test_real_service_wire_prompt_hash_matches_and_pii_is_redacted(caplog):
    seen = []

    def handler(request):
        content = json.loads(request.content)["messages"][-1]["content"]
        seen.append(content)
        return httpx.Response(200, json=_completion(_evaluation_from_prompt(content)))

    service = LLMService(_settings(), provider=_provider(handler), cache=DictCache())
    with caplog.at_level(logging.INFO, logger="dbcas.ai"):
        result = evaluate(DATA, service)
    assert not result["evaluator_fallback"]
    assert len(seen) == 1
    assert hashlib.sha256(seen[0].encode()).hexdigest() == result["prompt_hash"]
    assert PII not in seen[0] and PHONE not in seen[0] and "[id]" in seen[0]
    assert "test-key" not in caplog.text
    assert PII not in caplog.text and PHONE not in caplog.text
    assert "role=evaluator" in caplog.text and result["prompt_hash"] in caplog.text
    assert "reason=-" in caplog.text


def test_valid_evaluation_is_cached_after_validation():
    cache = DictCache()
    calls = []

    def handler(request):
        content = json.loads(request.content)["messages"][-1]["content"]
        calls.append(content)
        return httpx.Response(200, json=_completion(_evaluation_from_prompt(content)))

    service = LLMService(_settings(), provider=_provider(handler), cache=cache)
    first = evaluate(DATA, service)
    second = evaluate(DATA, service)
    assert first == second
    assert len(calls) == 1 and cache.stores == 1


@pytest.mark.parametrize("status", [429, 500, 503])
def test_provider_transient_failure_retries_then_uses_the_real_evaluator(status):
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(status)
        content = json.loads(request.content)["messages"][-1]["content"]
        return httpx.Response(200, json=_completion(_evaluation_from_prompt(content)))

    service = LLMService(_settings(), provider=_provider(handler, max_retries=1), cache=DictCache())
    result = evaluate(DATA, service)
    assert not result["evaluator_fallback"] and len(calls) == 2


def test_timeout_falls_back_to_rules_and_logs_a_secret_free_reason(caplog):
    def handler(request):
        raise httpx.ReadTimeout("provider-secret-token")

    service = LLMService(_settings(), provider=_provider(handler), cache=DictCache())
    with caplog.at_level(logging.INFO, logger="dbcas.ai"):
        result = evaluate(DATA, service)
    assert result["evaluator_fallback"]
    assert "reason=llm_timeout" in caplog.text
    assert "provider-secret-token" not in caplog.text
    assert PII not in caplog.text
    assert len(result["evaluation"]["question_comments"]) == 2


def test_invalid_provider_output_is_never_cached_and_uses_rule_fallback():
    cache = DictCache()

    def handler(request):
        return httpx.Response(200, json=_completion({"bad": "payload"}))

    service = LLMService(_settings(), provider=_provider(handler), cache=cache)
    result = evaluate(DATA, service)
    assert result["evaluator_fallback"]
    assert cache.stores == 0
    assert [item["attempt_id"] for item in result["evaluation"]["question_comments"]] == [201, 202]
