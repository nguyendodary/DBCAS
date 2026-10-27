"""Provider abstraction + OpenAI-compatible REST client (Task 3.4).

The architecture doc names the external dependency generically — "LLM
Provider" — so the business layer talks to the ``LLMProvider`` protocol and
exactly one concrete REST client exists: ``ChatCompletionsProvider``, which
speaks the widely-supported ``POST {base}/chat/completions`` contract
(OpenAI, Azure OpenAI, and most compatible gateways). No vendor SDK — the
dependency is just httpx, already used elsewhere.

Retries are bounded and only applied to transient failures (429, 5xx,
network/timeout): provider 4xx other than 429 is deterministic and returns
immediately.
"""

import logging
from copy import deepcopy
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol
from urllib.parse import urlsplit

import httpx

from .errors import LLMError

logger = logging.getLogger(__name__)


def strict_wire_schema(schema):
    """Strict-compatible providers require every generated object field.

    Generation may require optional domain fields (such as confidence) too;
    application validation retains its documented contract. Never mutate the
    caller's schema or relax domain validation to accommodate a provider.
    """
    wire = deepcopy(schema)
    if wire.get("strict") is not True:
        return wire
    def normalize(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                node["required"] = list(node.get("properties", {}))
                node["additionalProperties"] = False
            for value in node.values():
                normalize(value)
        elif isinstance(node, list):
            for item in node:
                normalize(item)
    normalize(wire["schema"])
    return wire


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "system" | "user"
    content: str


@dataclass(frozen=True)
class StructuredRequest:
    """One structured-generation call, pre-sanitization."""

    task_type: str
    model: str
    messages: tuple[ChatMessage, ...]
    temperature: float = 0.0
    seed: Optional[int] = None
    json_schema: Optional[dict] = None  # response_format json_schema, if set
    max_tokens: Optional[int] = None


class LLMProvider(Protocol):
    """What grading services depend on — swap implementations freely."""

    def generate(self, request: StructuredRequest) -> str:
        """Return the assistant's raw text content. Raises LLMError."""
        ...


class ChatCompletionsProvider:
    """OpenAI-compatible chat-completions client.

    ``transport`` lets tests inject ``httpx.MockTransport`` — no real network
    is ever required.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        backoff_seconds: float = 0.5,
        transport: Optional[httpx.BaseTransport] = None,
        sleeper=time.sleep,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._max_retries = max(0, max_retries)
        self._backoff = backoff_seconds
        self._transport = transport
        self._sleep = sleeper

    # ---------- public API ----------

    def generate(self, request: StructuredRequest) -> str:
        body: dict[str, Any] = {
            "model": request.model,
            "messages": [
                {"role": m.role, "content": m.content} for m in request.messages
            ],
            "temperature": request.temperature,
        }
        if request.seed is not None:
            body["seed"] = request.seed
        if request.json_schema is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": strict_wire_schema(request.json_schema),
            }
        else:
            body["response_format"] = {"type": "json_object"}
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens

        # OpenRouter can route a strict JSON task to a reasoning model which
        # consumes the entire output allowance without producing an answer.
        # Prefer visible structured output. Some routed endpoints mandate
        # reasoning; the transport handles that explicit compatibility error
        # once, inside the existing retry budget, without replacing the model.
        # Other compatible endpoints must never receive vendor-only parameters.
        if urlsplit(self._base_url).hostname == "openrouter.ai":
            body["reasoning"] = {"enabled": False}
            body["provider"] = {"require_parameters": True}

        response = self._post_with_retries(body)
        return self._extract_content(response)

    # ---------- internals ----------

    def _post_with_retries(self, body: dict) -> dict:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        attempt = 0
        while True:
            attempt += 1
            try:
                with httpx.Client(
                    timeout=self._timeout, transport=self._transport
                ) as client:
                    resp = client.post(url, json=body, headers=headers)
            except httpx.TimeoutException:
                if attempt <= self._max_retries:
                    self._sleep(self._backoff * attempt)
                    continue
                raise LLMError(
                    LLMError.TIMEOUT,
                    "The AI grading service timed out",
                )
            except httpx.HTTPError:
                if attempt <= self._max_retries:
                    self._sleep(self._backoff * attempt)
                    continue
                raise LLMError(
                    LLMError.UNAVAILABLE,
                    "The AI grading service is unavailable",
                )

            if resp.status_code < 400:
                try:
                    payload = resp.json()
                except ValueError:
                    raise LLMError(
                        LLMError.INVALID_RESPONSE,
                        "The AI grading service returned an unreadable response",
                    )
                if not isinstance(payload, dict):
                    raise LLMError(LLMError.INVALID_RESPONSE, "The AI grading service returned a malformed response")
                # Some compatible gateways report an upstream failure in an
                # HTTP 200 envelope. It is never a successful completion.
                if payload.get("error"):
                    error = payload["error"]
                    code = error.get("code") if isinstance(error, dict) else None
                    kind = LLMError.RATE_LIMITED if code == 429 else LLMError.PROVIDER_ERROR
                    raise LLMError(kind, "The AI provider did not complete the request")
                return payload

            if resp.status_code in (401, 403):
                raise LLMError(
                    LLMError.AUTH_FAILED,
                    "The AI grading service rejected the configured credentials",
                )
            if resp.status_code == 429:
                if attempt <= self._max_retries:
                    self._sleep(self._backoff * attempt)
                    continue
                raise LLMError(LLMError.RATE_LIMITED, "AI grading is rate-limited")
            if resp.status_code >= 500:
                if attempt <= self._max_retries:
                    self._sleep(self._backoff * attempt)
                    continue
                raise LLMError(
                    LLMError.PROVIDER_ERROR,
                    "The AI grading service reported an error",
                )
            if (resp.status_code == 400 and attempt <= self._max_retries
                    and urlsplit(self._base_url).hostname == "openrouter.ai"
                    and body.get("reasoning") == {"enabled": False}):
                try:
                    problem = resp.json().get("error", {})
                    mandatory = isinstance(problem, dict) and "reasoning is mandatory" in str(problem.get("message", "")).lower()
                except (ValueError, AttributeError):
                    mandatory = False
                if mandatory:
                    body = {**body, "reasoning": {"effort": "minimal"}}
                    continue
            raise LLMError(
                LLMError.PROVIDER_ERROR,
                f"The AI grading service rejected the request (HTTP {resp.status_code})",
            )

    @staticmethod
    def _extract_content(payload: dict) -> str:
        try:
            choice = payload["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError, AttributeError):
            raise LLMError(
                LLMError.INVALID_RESPONSE,
                "The AI grading service returned a malformed response",
            )
        if choice.get("finish_reason") == "length":
            raise LLMError(LLMError.INVALID_RESPONSE,
                           "The AI response exhausted its output budget before completion")
        if choice.get("message", {}).get("refusal") or choice.get("finish_reason") in ("content_filter", "error"):
            raise LLMError(LLMError.INVALID_RESPONSE, "The AI service did not produce a usable answer")
        if not isinstance(content, str) or not content.strip():
            raise LLMError(
                LLMError.INVALID_RESPONSE,
                "The AI grading service returned an empty response",
            )
        return content
