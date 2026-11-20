import json
import traceback

import httpx
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.services.llm import ChatMessage, LLMError, LLMService
from test_deployment_safety import deployment_settings


KEY = "fixture-router-credential"
MODEL = "fixture/model-v1"
PROMPT = "fixture student answer"


def release_settings(mode="production", **overrides):
    return deployment_settings(mode, **{
        "llm_provider": "openrouter", "openrouter_api_key": KEY,
        "openrouter_model": MODEL, "openrouter_provider_endpoint": "deepinfra/turbo",
        "llm_max_retries": 0, **overrides,
    })


@pytest.mark.parametrize("mode", ["staging", "production"])
@pytest.mark.parametrize(("overrides", "expected"), [
    ({"openrouter_data_collection": "allow"}, "OPENROUTER_DATA_COLLECTION"),
    ({"openrouter_zdr": False}, "OPENROUTER_ZDR"),
    ({"openrouter_provider_endpoint": ""}, "OPENROUTER_PROVIDER_ENDPOINT"),
    ({"openrouter_provider_endpoint": "fixture/*"}, "OPENROUTER_PROVIDER_ENDPOINT"),
    ({"openrouter_provider_endpoint": "deepinfra"}, "OPENROUTER_PROVIDER_ENDPOINT"),
    ({"openrouter_provider_endpoint": "deepinfra/fp8"}, "OPENROUTER_PROVIDER_ENDPOINT"),
    ({"openrouter_base_url": "https://router.example.test/api/v1"}, "OPENROUTER_BASE_URL"),
    ({"openrouter_model": "openrouter/auto"}, "OPENROUTER_MODEL"),
])
def test_release_rejects_unpinned_or_relaxed_openrouter(mode, overrides, expected):
    with pytest.raises(ValidationError, match=expected) as error:
        release_settings(mode, **overrides)
    assert KEY not in str(error.value)


def test_release_requires_explicit_openrouter_adapter():
    with pytest.raises(ValidationError, match="LLM_PROVIDER=openrouter"):
        deployment_settings(llm_base_url="https://openrouter.ai./api/v1", llm_api_key=KEY, llm_model=MODEL)


@pytest.mark.parametrize("mode", ["staging", "production"])
def test_release_pins_route_and_never_retries_with_relaxed_privacy(mode):
    calls = []

    def no_private_route(request):
        calls.append(json.loads(request.content))
        return httpx.Response(404, json={"error": {"message": "No matching private route"}})

    config = release_settings(mode, llm_max_retries=2)
    with pytest.raises(LLMError, match="HTTP 404"):
        mocked_service(config, no_private_route).generate_structured("test", [ChatMessage("user", PROMPT)])
    body, = calls
    assert body["provider"] == {
        "require_parameters": True, "data_collection": "deny", "zdr": True,
        "only": ["deepinfra/turbo"], "order": ["deepinfra/turbo"], "allow_fallbacks": False,
    }


@pytest.mark.parametrize("route", ["deepinfra", "deepinfra/fp8"])
def test_development_retains_flexible_openrouter_routing(route):
    def respond(request):
        assert json.loads(request.content)["provider"] == {
            "require_parameters": True, "data_collection": "allow", "zdr": False,
            "only": [route], "order": [route], "allow_fallbacks": False,
        }
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    config = settings(openrouter_provider_endpoint=route, openrouter_data_collection="allow", openrouter_zdr=False)
    assert mocked_service(config, respond).generate_structured("test", [ChatMessage("user", PROMPT)]) == {}


def test_cache_isolated_by_openrouter_endpoint():
    class Cache:
        def __init__(self):
            self.entries = {}

        def find(self, key):
            return self.entries.get(key)

        def store(self, key, _task, _model, result):
            self.entries[key] = result

    shared_cache = Cache()
    results = []
    for route, score in (("fixture/fp8", 1), ("another/bf16", 2)):
        def respond(_request, score=score):
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"score": score})}}]})

        service = mocked_service(settings(openrouter_provider_endpoint=route), respond)
        service._cache = shared_cache
        results.append(service.generate_structured("test", [ChatMessage("user", PROMPT)]))
    assert results == [{"score": 1}, {"score": 2}]


def settings(**overrides):
    return Settings(_env_file=None, **{
        "llm_provider": "openrouter", "openrouter_api_key": KEY,
        "openrouter_model": MODEL, "llm_max_retries": 0, **overrides,
    })


def mocked_service(config, handler):
    service = LLMService(config)
    service._get_provider()._transport = httpx.MockTransport(handler)
    return service


@pytest.mark.parametrize(("field", "env_name"), [
    ("openrouter_api_key", "OPENROUTER_API_KEY"), ("openrouter_model", "OPENROUTER_MODEL"),
])
def test_openrouter_fails_closed_even_with_valid_compatible_defaults(field, env_name):
    with pytest.raises(ValidationError, match=env_name) as error:
        settings(llm_api_key="unused-compatible-credential", llm_base_url="https://other.test/v1",
                 llm_model="other-model", **{field: " \t"})
    assert KEY not in str(error.value)
    assert "unused-compatible-credential" not in str(error.value)


def test_openrouter_default_url_and_private_routing_survive_a_budgeted_call():
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"ok":true}'}}]})

    config = settings(llm_timeout_seconds=40)
    assert KEY not in repr(config)
    result = mocked_service(config, respond).with_budget(timeout_seconds=9).generate_structured(
        "test", [ChatMessage("user", PROMPT)], sanitize_messages=False,
    )
    assert result == {"ok": True}
    request, = calls
    assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
    assert request.headers["Authorization"] == f"Bearer {KEY}"
    assert "HTTP-Referer" not in request.headers and "X-Title" not in request.headers
    assert request.extensions["timeout"]["read"] == 9
    body = json.loads(request.content)
    assert body["model"] == MODEL
    assert body["messages"] == [{"role": "user", "content": PROMPT}]
    assert body["response_format"] == {"type": "json_object"}
    assert body["provider"] == {"require_parameters": True, "data_collection": "deny", "zdr": True}


def test_openrouter_env_overrides_url_headers_and_routing(monkeypatch):
    for name, value in {
        "LLM_PROVIDER": "openrouter", "OPENROUTER_API_KEY": KEY, "OPENROUTER_MODEL": MODEL,
        "OPENROUTER_BASE_URL": "https://router.test/custom/v1/",
        "OPENROUTER_HTTP_REFERER": "https://dbcas.example.test", "OPENROUTER_APP_TITLE": "DBCAS",
        "OPENROUTER_DATA_COLLECTION": "allow", "OPENROUTER_ZDR": "false",
    }.items():
        monkeypatch.setenv(name, value)

    def respond(request):
        assert str(request.url) == "https://router.test/custom/v1/chat/completions"
        assert request.headers["HTTP-Referer"] == "https://dbcas.example.test"
        assert request.headers["X-Title"] == "DBCAS"
        assert json.loads(request.content)["provider"] == {
            "require_parameters": True, "data_collection": "allow", "zdr": False,
        }
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    assert mocked_service(Settings(_env_file=None), respond).generate_structured(
        "test", [ChatMessage("user", PROMPT)],
    ) == {}


@pytest.mark.parametrize(("status", "error_code", "expected"), [
    (401, 401, LLMError.AUTH_FAILED),
    (402, 402, LLMError.INSUFFICIENT_CREDITS),
    (429, 429, LLMError.RATE_LIMITED),
    (502, 502, LLMError.PROVIDER_ERROR),
    (503, 503, LLMError.PROVIDER_ERROR),
    (408, 408, LLMError.TIMEOUT),
    (200, 402, LLMError.INSUFFICIENT_CREDITS),
    (200, 429, LLMError.RATE_LIMITED),
    (None, None, LLMError.TIMEOUT),
])
def test_openrouter_maps_failures_without_logging_sensitive_content(status, error_code, expected, caplog):
    def respond(request):
        if status is None:
            raise httpx.ReadTimeout(f"{KEY} {PROMPT}", request=request)
        return httpx.Response(status, json={"error": {"code": error_code, "message": f"{KEY} {PROMPT}"}})

    with caplog.at_level("DEBUG"), pytest.raises(LLMError) as error:
        mocked_service(settings(), respond).generate_structured(
            "test", [ChatMessage("user", PROMPT)], sanitize_messages=False,
        )
    assert error.value.code == expected
    output = "".join(traceback.format_exception(error.value)) + caplog.text
    assert KEY not in output
    assert PROMPT not in output
