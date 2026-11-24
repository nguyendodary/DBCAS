"""Generic OpenAI-compatible LLM provider configuration and transport gates."""
import json
import logging
from pathlib import Path

import httpx
import pytest

from app.config import OPENAI_COMPATIBLE, Settings
from app.services.llm import ChatMessage, ChatCompletionsProvider, LLMError, LLMService

KEY = "fixture-provider-credential"
MODEL = "fixture/model-v1"
PROMPT = "fixture student answer"
ROOT = Path(__file__).resolve().parents[2]


def settings(**overrides):
    return Settings(_env_file=None, **{
        "llm_provider": OPENAI_COMPATIBLE, "llm_api_key": KEY,
        "llm_base_url": "https://provider.test/v1", "llm_model": MODEL,
        "llm_max_retries": 0, **overrides,
    })


def mocked_service(config, handler):
    service = LLMService(config)
    service._get_provider()._transport = httpx.MockTransport(handler)
    return service


@pytest.mark.parametrize("value", ["MISTRAL", "OpenAI", "groq", "anything-custom"])
def test_unknown_provider_names_are_accepted_with_a_warning(value, caplog):
    with caplog.at_level(logging.WARNING):
        config = settings(llm_provider=value)
    assert config.llm_provider == OPENAI_COMPATIBLE
    assert value in caplog.text
    assert "openai_compatible" in caplog.text


@pytest.mark.parametrize("value", ["compatible", "OPENAI_COMPATIBLE", " openai_compatible "])
def test_known_provider_aliases_do_not_warn(value, caplog):
    with caplog.at_level(logging.WARNING):
        assert settings(llm_provider=value).llm_provider == OPENAI_COMPATIBLE
    assert "Unknown LLM_PROVIDER" not in caplog.text


@pytest.mark.parametrize("base", ["https://provider.test/v1", "https://openrouter.ai/api/v1"])
def test_no_vendor_only_parameters_are_sent_to_any_compatible_base(base):
    seen = []

    def handler(request):
        seen.append((json.loads(request.content), request.headers))
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"ok":true}'}}]})

    provider = ChatCompletionsProvider(base, "test-only", transport=httpx.MockTransport(handler))
    body, headers = None, None
    provider.generate(__request())
    body, headers = seen[0]
    assert "provider" not in body and "reasoning" not in body
    assert "HTTP-Referer" not in headers and "X-Title" not in headers
    assert body["model"] == "owner-model" and body["response_format"] == {"type": "json_object"}


def __request(**updates):
    values = {"task_type": "gen_question", "model": "owner-model",
              "messages": (ChatMessage("user", "synthetic"),), "seed": 42,
              "max_tokens": 512}
    values.update(updates)
    from app.services.llm import StructuredRequest
    return StructuredRequest(**values)


@pytest.mark.parametrize("status", [400, 422])
def test_unsupported_optional_fields_are_retried_once_without_them(status, caplog):
    bodies = []

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        if "response_format" in body or "seed" in body:
            return httpx.Response(status, json={"detail": [{"loc": ["body", "seed"], "msg": "extra field"}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"ok":true}'}}]})

    provider = ChatCompletionsProvider("https://provider.test/v1", "test-only",
                                       transport=httpx.MockTransport(handler))
    with caplog.at_level(logging.WARNING):
        assert provider.generate(__request()) == '{"ok":true}'
    assert len(bodies) == 2
    assert "response_format" in bodies[0] and "seed" in bodies[0]
    assert "response_format" not in bodies[1] and "seed" not in bodies[1]
    assert bodies[1]["model"] == "owner-model"
    assert "response_format,seed" in caplog.text or "seed,response_format" in caplog.text


def test_400_is_retried_at_most_once_and_then_fails_closed():
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(400, json={"message": "invalid model"})

    provider = ChatCompletionsProvider("https://provider.test/v1", "test-only",
                                       transport=httpx.MockTransport(handler))
    with pytest.raises(LLMError) as error:
        provider.generate(__request())
    assert error.value.code == LLMError.PROVIDER_ERROR
    assert len(calls) == 2
    assert not set(calls[1]).intersection({"response_format", "seed", "max_tokens"})


@pytest.mark.parametrize(("status", "code", "expected"), [
    (401, 401, LLMError.AUTH_FAILED), (403, 403, LLMError.AUTH_FAILED),
    (402, 402, LLMError.INSUFFICIENT_CREDITS), (408, 408, LLMError.TIMEOUT),
    (429, 429, LLMError.RATE_LIMITED), (502, 502, LLMError.PROVIDER_ERROR),
    (200, 402, LLMError.INSUFFICIENT_CREDITS), (200, 429, LLMError.RATE_LIMITED),
])
def test_error_mapping_never_logs_credentials_or_prompts(status, code, expected, caplog):
    def handler(_request):
        return httpx.Response(status, json={"error": {"code": code, "message": f"{KEY} {PROMPT}"}})

    with caplog.at_level(logging.DEBUG), pytest.raises(LLMError) as error:
        mocked_service(settings(), handler).generate_structured(
            "test", [ChatMessage("user", PROMPT)], sanitize_messages=False,
        )
    assert error.value.code == expected
    assert KEY not in caplog.text and PROMPT not in caplog.text


def test_missing_key_disables_ai_without_raising():
    config = Settings(_env_file=None, llm_api_key="", llm_base_url="https://provider.test/v1",
                      llm_model=MODEL)
    service = LLMService(config)
    assert not service.is_configured()
    with pytest.raises(LLMError) as error:
        service.generate_structured("test", [ChatMessage("user", "synthetic")])
    assert error.value.code == LLMError.NOT_CONFIGURED


@pytest.mark.parametrize("mode", ["staging", "production"])
def test_release_requires_an_https_base_url(mode):
    with pytest.raises(ValueError, match="HTTPS LLM_BASE_URL"):
        Settings(_env_file=None, deployment_mode=mode, llm_api_key=KEY,
                 llm_base_url="http://provider.test/v1", llm_model=MODEL)


@pytest.mark.parametrize("overrides", [{"llm_base_url": ""}, {"llm_model": ""}])
def test_missing_url_or_model_leaves_ai_unconfigured(overrides):
    values = {"llm_api_key": KEY, "llm_model": MODEL,
              "llm_base_url": "https://provider.test/v1"}
    values.update(overrides)
    config = Settings(_env_file=None, **values)
    assert not LLMService(config).is_configured()


def test_no_openrouter_environment_keys_remain():
    paths = [ROOT / ".env.example", ROOT / "docker-compose.local.yml",
             ROOT / "docker-compose.dn.yml", ROOT / "docker-compose.qa.yml",
             ROOT / "deploy" / "release.env.example",
             ROOT / "backend" / "app" / "config.py",
             ROOT / "backend" / "app" / "services" / "llm" / "provider.py",
             ROOT / "backend" / "app" / "services" / "llm" / "service.py"]
    for path in paths:
        assert "OPENROUTER_" not in path.read_text(encoding="utf-8"), path.name
