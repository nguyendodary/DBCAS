"""LLMService — configuration, caching, and structured generation.

Sits between the grading services and the provider client:

    EssayScoringService / SQL helpers
        -> LLMService.generate_structured()   (cache + JSON parse)
            -> LLMProvider.generate()          (REST call)

Behaviour contract (Task 3.4 / NFR-09):
* No API key -> LLMError(NOT_CONFIGURED): controlled, never a crash, and the
  rest of the app keeps working.
* Responses are cached in ``llm_cache`` keyed by a sha256 of the canonical
  request — identical prompts never hit the provider twice.
* Output is always parsed as JSON; malformed content raises
  INVALID_RESPONSE instead of leaking into grading logic.
"""

import hashlib
import json
import logging
from typing import Optional, Protocol, Callable

from ...config import Settings
from ...repositories import LlmCacheRepository
from .errors import LLMError
from .sanitize import sanitize_learner_text
from .validation import validate_json_schema
from .provider import (
    ChatCompletionsProvider,
    ChatMessage,
    LLMProvider,
    StructuredRequest,
)

logger = logging.getLogger(__name__)
_MISSING = object()


class CacheStore(Protocol):
    """Minimal cache surface — LlmCacheRepository in production, a plain
    dict-backed fake in unit tests."""

    def find(self, request_hash: str) -> Optional[dict]: ...
    def store(
        self, request_hash: str, task_type: str, model: str, response: dict
    ) -> None: ...


class LLMService:
    def __init__(
        self,
        settings: Settings,
        *,
        provider: Optional[LLMProvider] = None,
        cache: Optional[CacheStore] = None,
    ):
        self._settings = settings
        self._provider = provider
        self._cache = cache

    def with_budget(self, *, timeout_seconds=10, max_retries=1):
        settings = self._settings.model_copy(update={
            "llm_timeout_seconds": min(self._settings.llm_timeout_seconds, timeout_seconds),
            "llm_max_retries": min(self._settings.llm_max_retries, max_retries),
        })
        provider = (self._provider.with_budget(timeout_seconds=settings.llm_timeout_seconds, max_retries=settings.llm_max_retries)
                    if isinstance(self._provider, ChatCompletionsProvider) else self._provider)
        return LLMService(settings, provider=provider, cache=self._cache)

    # ---------- configuration ----------

    def is_configured(self) -> bool:
        return bool(
            self._settings.llm_api_key.strip()
            and self._settings.llm_base_url.strip()
            and self._settings.llm_model.strip()
        )

    def _get_provider(self) -> LLMProvider:
        if self._provider is not None:
            return self._provider
        if not self.is_configured():
            raise LLMError(
                LLMError.NOT_CONFIGURED,
                "AI grading is not configured on this deployment",
            )
        self._provider = ChatCompletionsProvider(
            self._settings.llm_base_url,
            self._settings.llm_api_key,
            timeout_seconds=self._settings.llm_timeout_seconds,
            max_retries=self._settings.llm_max_retries,
            backoff_seconds=self._settings.llm_backoff_seconds,
        )
        return self._provider

    # ---------- generation ----------

    def generate_structured(
        self,
        task_type: str,
        messages: list[ChatMessage],
        *,
        json_schema: Optional[dict] = None,
        max_tokens: Optional[int] = None,
        validator: Optional[Callable[[dict], dict]] = None,
        identifiers=(),
        context_version: str = "1",
        sanitize_messages: bool = True,
    ) -> dict:
        """One structured generation. Returns the parsed JSON object.

        ``sanitize_messages=False`` is for callers that already sanitized the
        evidence before hashing it; it guarantees the wire prompt is byte-equal
        to the hash they expose.
        """
        provider = self._get_provider()  # raises NOT_CONFIGURED w/o key
        request = StructuredRequest(
            task_type=task_type,
            model=self._settings.llm_model,
            messages=(tuple(ChatMessage(m.role, sanitize_learner_text(m.content, identifiers=identifiers)) for m in messages)
                      if sanitize_messages else tuple(messages)),
            temperature=self._settings.llm_temperature,
            seed=self._settings.llm_seed,
            json_schema=json_schema,
            max_tokens=max_tokens,
        )
        request_hash = _request_hash(request, provider=self._settings.llm_base_url,
                                     prompt_version=self._settings.llm_prompt_version,
                                     context_version=context_version)

        cached = self._cache.find(request_hash) if self._cache else None
        if cached is not None:
            logger.info("llm cache hit task=%s hash=%s", task_type, request_hash[:12])
            return self._validate(cached, json_schema, validator)

        raw = provider.generate(request)
        parsed = self._parse_json(raw)
        parsed = self._validate(parsed, json_schema, validator)
        if self._cache is not None:
            try:
                self._cache.store(
                    request_hash, task_type, self._settings.llm_model, parsed
                )
            except Exception as exc:  # cache write must never fail grading
                logger.warning("llm cache store failed: %s", type(exc).__name__)
        return parsed

    @staticmethod
    def _validate(parsed, json_schema, validator):
        try:
            validate_json_schema(parsed, (json_schema.get("schema", json_schema) if json_schema else {}))
        except LLMError as exc:
            exc.reason_code = "schema"
            raise
        return validator(parsed) if validator else parsed

    @staticmethod
    def _parse_json(raw: str) -> dict:
        if not isinstance(raw, str) or len(raw.encode()) > 262144:
            error = LLMError(LLMError.INVALID_RESPONSE, "The AI service returned an oversized or invalid response")
            error.reason_code = "json_parse"
            raise error
        text = raw.lstrip("\ufeff").strip()
        try:
            strict = json.loads(
                text,
                parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite number")),
            )
        except (ValueError, TypeError, RecursionError, OverflowError):
            strict = _MISSING
        if strict is not _MISSING and not isinstance(strict, dict):
            error = LLMError(
                LLMError.INVALID_RESPONSE,
                "The AI grading service did not return a JSON object",
            )
            error.reason_code = "schema"
            raise error
        parsed = _decode_json_object(raw)
        if parsed is None:
            error = LLMError(
                LLMError.INVALID_RESPONSE,
                "The AI grading service returned invalid JSON",
            )
            error.reason_code = "json_parse"
            raise error
        if not isinstance(parsed, dict):
            error = LLMError(
                LLMError.INVALID_RESPONSE,
                "The AI grading service did not return a JSON object",
            )
            error.reason_code = "schema"
            raise error
        return parsed


def _decode_json_object(raw: str):
    """Decode the first JSON object even when a provider adds prose or fences.

    This is deliberately limited to locating/decoding the object. Field-level
    schema, scope, SQL and content validation remain strict downstream.
    """
    decoder = json.JSONDecoder(
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite number"))
    )
    text = raw.lstrip("\ufeff").strip()
    candidates = [text]
    cursor = text.find("```")
    while cursor >= 0:
        closing = text.find("```", cursor + 3)
        if closing < 0:
            break
        block = text[cursor + 3:closing].strip()
        if block.lower().startswith("json"):
            block = block[4:].lstrip()
        if block:
            candidates.append(block)
        cursor = text.find("```", closing + 3)
    for candidate in candidates:
        start = candidate.find("{")
        array = candidate.find("[")
        if array >= 0 and (start < 0 or array < start):
            # A top-level JSON array is never accepted as a structured object.
            continue
        attempts = 0
        while start >= 0 and attempts < 1000:
            attempts += 1
            try:
                value, _ = decoder.raw_decode(candidate[start:])
            except (ValueError, TypeError, RecursionError, OverflowError):
                start = candidate.find("{", start + 1)
                continue
            if isinstance(value, dict):
                return value
            break
    return None


def _request_hash(request: StructuredRequest, *, provider="", prompt_version="1", context_version="1") -> str:
    """sha256 over the canonical request — model + messages + schema decide
    the cache key, so a config change never replays a stale response."""
    canonical = json.dumps(
        {
            "task_type": request.task_type,
            "provider": provider,
            "prompt_version": prompt_version,
            "context_version": context_version,
            "max_tokens": request.max_tokens,
            "model": request.model,
            "messages": [
                {"role": m.role, "content": m.content} for m in request.messages
            ],
            "json_schema": request.json_schema,
            "temperature": request.temperature,
            "seed": request.seed,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_llm_service(settings: Settings, db=None) -> LLMService:
    """Factory used by FastAPI deps: wires the DB-backed cache when a
    session is available."""
    cache = LlmCacheRepository(db) if db is not None else None
    return LLMService(settings, cache=cache)
