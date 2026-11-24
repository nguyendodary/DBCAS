"""Generic OpenAI-compatible transport behaviour; no vendor-specific paths."""
import json

import httpx
import pytest

from app.services.llm import ChatCompletionsProvider, ChatMessage, LLMError, StructuredRequest


@pytest.mark.parametrize("base,expected", [
    ("https://provider.test/v1", "https://provider.test/v1/chat/completions"),
    ("https://provider.test/v1/", "https://provider.test/v1/chat/completions"),
    ("https://provider.test/v1/chat/completions", "https://provider.test/v1/chat/completions"),
    ("https://provider.test/v1/chat/completions/", "https://provider.test/v1/chat/completions"),
    ("https://mistral.example.test/v1/chat/completions", "https://mistral.example.test/v1/chat/completions"),
    ("https://provider.test/v1/chat/completions?api-version=qa", "https://provider.test/v1/chat/completions?api-version=qa"),
    ("https://provider.test/v1?api-version=qa", "https://provider.test/v1/chat/completions?api-version=qa"),
])
@pytest.mark.parametrize("bounded", [False, True])
def test_base_or_complete_url_posts_once_to_the_configured_completion_endpoint(base, expected, bounded):
    seen = []
    def handler(request):
        seen.append(request)
        if str(request.url) != expected:
            return httpx.Response(404, json={"error": {"code": 404}})
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": '{"ok":true}'}}]})
    provider = ChatCompletionsProvider(base, "test-only", max_retries=0,
        transport=httpx.MockTransport(handler))
    if bounded:
        provider = provider.with_budget(timeout_seconds=5, max_retries=0)
    request = StructuredRequest("gen_question", "owner-selected-model", (ChatMessage("user", "synthetic"),), max_tokens=512)
    assert provider.generate(request) == '{"ok":true}'
    assert len(seen) == 1 and str(seen[0].url) == expected
    assert seen[0].headers["Authorization"] == "Bearer test-only"
    body = json.loads(seen[0].content)
    assert body["model"] == "owner-selected-model" and body["max_tokens"] == 512
    assert body["response_format"] == {"type": "json_object"}


@pytest.mark.parametrize("base,model,openai_default", [
    ("https://api.openai.com/v1", "gpt-5.4-mini", True),
    ("https://api.openai.com/v1", "gpt-5.4-mini-2026-03-17", True),
    ("https://provider.test/v1", "gpt-5.4-mini", False),
    ("https://api.openai.com.attacker.test/v1", "gpt-5.4-mini", False),
    ("https://api.openai.com/v1", "owner-selected-model", False),
])
def test_local_openai_default_uses_supported_parameters_without_changing_custom_models(base, model, openai_default):
    seen = []
    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": '{"score":1}'}}]})
    provider = ChatCompletionsProvider(base, "test-only", transport=httpx.MockTransport(handler))
    request = StructuredRequest("essay_score", model, (ChatMessage("user", "Grade this synthetic essay as JSON"),),
                                temperature=0.1, seed=42, max_tokens=512)
    assert provider.generate(request) == '{"score":1}'
    body = seen[0]
    assert body["model"] == model and body["temperature"] == 0.1
    assert body["messages"] == [{"role": "user", "content": "Grade this synthetic essay as JSON"}]
    assert body["response_format"] == {"type": "json_object"}
    if openai_default:
        assert body["reasoning_effort"] == "none" and body["max_completion_tokens"] == 512
        assert "max_tokens" not in body and "seed" not in body
    else:
        assert body["max_tokens"] == 512 and body["seed"] == 42
        assert "reasoning_effort" not in body and "max_completion_tokens" not in body


@pytest.mark.parametrize("choice,fragment", [
    ({"finish_reason": "length", "message": {"content": None, "reasoning": "private"}}, "output budget"),
    ({"finish_reason": "length", "message": {"content": '{"score":1}'}}, "output budget"),
    ({"finish_reason": "stop", "message": {"content": None, "reasoning": "private"}}, "empty"),
    ({"finish_reason": "stop", "message": {"content": '{"score":1}', "refusal": "refused"}}, "usable"),
])
def test_truncation_reasoning_and_refusal_cannot_be_scores(choice, fragment):
    with pytest.raises(LLMError, match=fragment):
        ChatCompletionsProvider._extract_content({"choices": [choice]})


def test_http_200_error_envelope_is_not_a_completion():
    provider = ChatCompletionsProvider("https://provider.test/v1", "test-only", max_retries=0,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"error": {"code": 429, "message": "private upstream details"}})))
    with pytest.raises(LLMError) as error:
        provider.generate(StructuredRequest("essay_score", "owner-model", (ChatMessage("user", "synthetic"),)))
    assert error.value.code == LLMError.RATE_LIMITED and "private" not in str(error.value)
