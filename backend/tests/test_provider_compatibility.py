import json
import httpx
import pytest

from app.services.llm import ChatCompletionsProvider, ChatMessage, LLMError, StructuredRequest


@pytest.mark.parametrize("base,router", [("https://openrouter.ai/api/v1", True), ("https://provider.test/v1", False),
                                      ("https://openrouter.ai.attacker.test/v1", False)])
def test_endpoint_controls_preserve_owner_model(base, router):
    seen = []
    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": '{"ok":true}'}}]})
    provider = ChatCompletionsProvider(base, "test-only", transport=httpx.MockTransport(handler))
    request = StructuredRequest("essay_score", "owner-selected-model", (ChatMessage("user", "synthetic"),), max_tokens=512)
    assert provider.generate(request) == '{"ok":true}'
    assert seen[0]["model"] == "owner-selected-model" and seen[0]["max_tokens"] == 512
    assert ("reasoning" in seen[0]) is router
    if router:
        assert seen[0]["reasoning"] == {"enabled": False}
        assert seen[0]["provider"] == {"require_parameters": True}


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


@pytest.mark.parametrize("retry_budget", [0, 1])
def test_mandatory_reasoning_compatibility_uses_existing_retry_budget(retry_budget):
    seen = []
    def handler(request):
        body = json.loads(request.content)
        seen.append(body)
        if body["reasoning"] == {"enabled": False}:
            return httpx.Response(400, json={"error": {"message": "Reasoning is mandatory for this endpoint and cannot be disabled."}})
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": '{"ok":true}'}}]})
    provider = ChatCompletionsProvider("https://openrouter.ai/api/v1", "test-only", max_retries=retry_budget,
        transport=httpx.MockTransport(handler))
    request = StructuredRequest("gen_question", "owner-selected-model", (ChatMessage("user", "synthetic"),), max_tokens=4096)
    if retry_budget == 0:
        with pytest.raises(LLMError):
            provider.generate(request)
        assert len(seen) == 1
    else:
        assert provider.generate(request) == '{"ok":true}'
        assert len(seen) == 2 and seen[1]["reasoning"] == {"effort": "minimal"}
        assert seen[1]["model"] == seen[0]["model"] == "owner-selected-model"
        assert seen[1]["max_tokens"] == seen[0]["max_tokens"] == 4096
