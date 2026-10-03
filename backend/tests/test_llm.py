"""External LLM integration tests — Task 3.4 (DBCAS-19).

Every test is fully mocked via ``httpx.MockTransport`` + a dict-backed cache —
no real provider call is ever made. Covers the completion gate: success,
missing key, timeout, 429/5xx retry, auth failure, malformed/empty/non-object
JSON, cache hit/store, and PII sanitization of outgoing content.
"""

import json

import httpx
import pytest

from app.config import Settings
from app.services.llm import (
    ChatCompletionsProvider,
    ChatMessage,
    LLMError,
    LLMService,
    StructuredRequest,
    sanitize_learner_text,
)


class DictCache:
    def __init__(self):
        self._data = {}
        self.store_calls = 0

    def find(self, request_hash):
        return self._data.get(request_hash)

    def store(self, request_hash, task_type, model, response):
        self._data[request_hash] = response
        self.store_calls += 1


def _settings(**over):
    base = {
        "llm_api_key": "test-key",
        "llm_base_url": "https://llm.test/v1",
        "llm_model": "grader-1",
        "llm_backoff_seconds": 0.0,
    }
    base.update(over)
    return Settings(**base)


def _request(messages=None):
    return StructuredRequest(
        task_type="essay_grading",
        model="grader-1",
        messages=tuple(messages or [ChatMessage("user", "grade this")]),
        temperature=0.0,
        seed=42,
        json_schema={"name": "essay_grade", "schema": {"type": "object"}},
    )


def _ok_payload(content=None):
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content if content is not None else '{"score": 8}',
                }
            }
        ]
    }


def _provider(handler, **kw):
    kw.setdefault("backoff_seconds", 0.0)
    kw.setdefault("sleeper", lambda s: None)
    return ChatCompletionsProvider(
        "https://llm.test/v1",
        "test-key",
        transport=httpx.MockTransport(handler),
        **kw,
    )


class TestProviderClient:
    def test_success_returns_content(self):
        def handler(request):
            body = json.loads(request.content)
            assert request.headers["Authorization"] == "Bearer test-key"
            assert body["model"] == "grader-1"
            assert body["temperature"] == 0.0
            assert body["seed"] == 42
            assert body["response_format"]["type"] == "json_schema"
            return httpx.Response(200, json=_ok_payload('{"score": 9}'))

        out = _provider(handler).generate(_request())
        assert out == '{"score": 9}'

    def test_429_retries_then_succeeds(self):
        calls = []

        def handler(request):
            calls.append(1)
            if len(calls) < 3:
                return httpx.Response(429, json={"error": "slow down"})
            return httpx.Response(200, json=_ok_payload())

        out = _provider(handler, max_retries=3).generate(_request())
        assert out == '{"score": 8}' and len(calls) == 3

    def test_429_exhausts_retries(self):
        def handler(request):
            return httpx.Response(429)

        with pytest.raises(LLMError) as exc:
            _provider(handler, max_retries=1).generate(_request())
        assert exc.value.code == LLMError.RATE_LIMITED

    def test_5xx_retries_then_provider_error(self):
        calls = []

        def handler(request):
            calls.append(1)
            return httpx.Response(500)

        with pytest.raises(LLMError) as exc:
            _provider(handler, max_retries=2).generate(_request())
        assert exc.value.code == LLMError.PROVIDER_ERROR
        assert len(calls) == 3  # initial + 2 retries

    def test_401_no_retry(self):
        calls = []

        def handler(request):
            calls.append(1)
            return httpx.Response(401)

        with pytest.raises(LLMError) as exc:
            _provider(handler, max_retries=2).generate(_request())
        assert exc.value.code == LLMError.AUTH_FAILED
        assert len(calls) == 1  # deterministic failure — no retry

    def test_400_no_retry(self):
        def handler(request):
            return httpx.Response(400, json={"error": "bad request"})

        with pytest.raises(LLMError) as exc:
            _provider(handler).generate(_request())
        assert exc.value.code == LLMError.PROVIDER_ERROR

    def test_timeout_normalized(self):
        def handler(request):
            raise httpx.ReadTimeout("timed out")

        with pytest.raises(LLMError) as exc:
            _provider(handler, max_retries=1).generate(_request())
        assert exc.value.code == LLMError.TIMEOUT

    def test_network_error_normalized(self):
        def handler(request):
            raise httpx.ConnectError("unreachable")

        with pytest.raises(LLMError) as exc:
            _provider(handler, max_retries=0).generate(_request())
        assert exc.value.code == LLMError.UNAVAILABLE

    @pytest.mark.parametrize(
        "payload",
        [
            {},  # no choices
            {"choices": []},  # empty choices
            {"choices": [{"message": {}}]},  # no content
            {"choices": [{"message": {"content": ""}}]},  # empty
            {"choices": [{"message": {"content": "   "}}]},  # blank
            {"choices": [{"message": {"content": 123}}]},  # non-string
        ],
    )
    def test_malformed_envelopes(self, payload):
        def handler(request):
            return httpx.Response(200, json=payload)

        with pytest.raises(LLMError) as exc:
            _provider(handler).generate(_request())
        assert exc.value.code == LLMError.INVALID_RESPONSE

    def test_non_json_body(self):
        def handler(request):
            return httpx.Response(200, text="<html>oops</html>")

        with pytest.raises(LLMError) as exc:
            _provider(handler).generate(_request())
        assert exc.value.code == LLMError.INVALID_RESPONSE


class TestService:
    def _service(self, handler, **settings_over):
        return LLMService(
            _settings(**settings_over),
            provider=_provider(handler),
            cache=DictCache(),
        )

    def test_success_parses_json(self):
        svc = self._service(
            lambda r: httpx.Response(200, json=_ok_payload('{"a": 1}'))
        )
        assert svc.generate_structured("t", [ChatMessage("user", "x")]) == {"a": 1}

    def test_missing_key(self):
        svc = LLMService(_settings(llm_api_key=""), cache=DictCache())
        assert svc.is_configured() is False
        with pytest.raises(LLMError) as exc:
            svc.generate_structured("t", [ChatMessage("user", "x")])
        assert exc.value.code == LLMError.NOT_CONFIGURED

    def test_missing_base_url(self):
        svc = LLMService(_settings(llm_base_url=""), cache=DictCache())
        assert svc.is_configured() is False

    def test_malformed_json_content(self):
        svc = self._service(
            lambda r: httpx.Response(200, json=_ok_payload("not json{{"))
        )
        with pytest.raises(LLMError) as exc:
            svc.generate_structured("t", [ChatMessage("user", "x")])
        assert exc.value.code == LLMError.INVALID_RESPONSE

    def test_non_object_json_rejected(self):
        svc = self._service(
            lambda r: httpx.Response(200, json=_ok_payload('[1, 2]'))
        )
        with pytest.raises(LLMError) as exc:
            svc.generate_structured("t", [ChatMessage("user", "x")])
        assert exc.value.code == LLMError.INVALID_RESPONSE

    def test_code_fence_tolerated(self):
        svc = self._service(
            lambda r: httpx.Response(
                200, json=_ok_payload('```json\n{"ok": true}\n```')
            )
        )
        assert svc.generate_structured("t", [ChatMessage("user", "x")]) == {
            "ok": True
        }

    def test_cache_hit_skips_provider(self):
        calls = []

        def handler(request):
            calls.append(1)
            return httpx.Response(200, json=_ok_payload('{"v": 7}'))

        svc = self._service(handler)
        msgs = [ChatMessage("user", "same prompt")]
        first = svc.generate_structured("essay_grading", msgs)
        second = svc.generate_structured("essay_grading", msgs)
        assert first == second == {"v": 7}
        assert len(calls) == 1  # second call served from llm_cache path

    def test_different_prompts_different_hash(self):
        calls = []

        def handler(request):
            calls.append(1)
            return httpx.Response(200, json=_ok_payload('{"v": 1}'))

        svc = self._service(handler)
        svc.generate_structured("t", [ChatMessage("user", "one")])
        svc.generate_structured("t", [ChatMessage("user", "two")])
        assert len(calls) == 2

    def test_provider_error_propagates(self):
        svc = self._service(lambda r: httpx.Response(503))
        with pytest.raises(LLMError) as exc:
            svc.generate_structured("t", [ChatMessage("user", "x")])
        assert exc.value.code == LLMError.PROVIDER_ERROR


class TestSanitize:
    def test_name_and_email_redacted(self):
        out = sanitize_learner_text(
            "I, Nguyen Van A, think the answer is 3. My id is 20210045.",
            identifiers=["Nguyen Van A"],
        )
        assert "Nguyen" not in out and "20210045" not in out
        assert "[name]" in out and "[id]" in out
        assert "3" in out  # content numbers survive

    def test_email_pattern(self):
        out = sanitize_learner_text("mail me at a.b@school.edu please")
        assert "a.b@school.edu" not in out

    def test_phone_and_grouped_ids(self):
        out = sanitize_learner_text("call 090-123-4567 or see record 12-34-56")
        assert "090-123-4567" not in out and "12-34-56" not in out

    def test_no_identifiers_still_scrubs_patterns(self):
        out = sanitize_learner_text("student number 99887766 wrote this")
        assert "99887766" not in out

    def test_short_numbers_preserved(self):
        out = sanitize_learner_text("3NF removes transitive dependency in 2 steps")
        assert "3NF" in out and "2" in out


class TestProviderGetsSanitizedContent:
    """End-to-end-ish: sanitizer output is what actually goes on the wire."""

    def test_wire_content_is_sanitized(self):
        seen = []

        def handler(request):
            body = json.loads(request.content)
            seen.append(body["messages"][0]["content"])
            return httpx.Response(200, json=_ok_payload('{"ok": true}'))

        dirty = "I am Bui Thi C, id 20219988 — here is my essay."
        clean = sanitize_learner_text(dirty, identifiers=["Bui Thi C"])
        svc = LLMService(
            _settings(), provider=_provider(handler), cache=DictCache()
        )
        svc.generate_structured("essay_grading", [ChatMessage("user", clean)])
        assert "Bui Thi C" not in seen[0] and "20219988" not in seen[0]
        assert "[name]" in seen[0] and "[id]" in seen[0]
