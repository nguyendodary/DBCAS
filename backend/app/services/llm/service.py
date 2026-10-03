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
from typing import Any, Optional, Protocol

from ...config import Settings
from ...repositories import LlmCacheRepository
from .errors import LLMError
from .provider import (
    ChatCompletionsProvider,
    ChatMessage,
    LLMProvider,
    StructuredRequest,
)

logger = logging.getLogger(__name__)


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

    # ---------- configuration ----------

    def is_configured(self) -> bool:
        return bool(
            self._settings.llm_api_key
            and self._settings.llm_base_url
            and self._settings.llm_model
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
    ) -> dict:
        """One structured generation. Returns the parsed JSON object."""
        provider = self._get_provider()  # raises NOT_CONFIGURED w/o key
        request = StructuredRequest(
            task_type=task_type,
            model=self._settings.llm_model,
            messages=tuple(messages),
            temperature=self._settings.llm_temperature,
            seed=self._settings.llm_seed,
            json_schema=json_schema,
            max_tokens=max_tokens,
        )
        request_hash = _request_hash(request)

        cached = self._cache.find(request_hash) if self._cache else None
        if cached is not None:
            logger.info("llm cache hit task=%s hash=%s", task_type, request_hash[:12])
            return cached

        raw = provider.generate(request)
        parsed = self._parse_json(raw)
        if self._cache is not None:
            try:
                self._cache.store(
                    request_hash, task_type, self._settings.llm_model, parsed
                )
            except Exception as exc:  # cache write must never fail grading
                logger.warning("llm cache store failed: %s", type(exc).__name__)
        return parsed

    @staticmethod
    def _parse_json(raw: str) -> dict:
        text = raw.strip()
        # Providers occasionally wrap JSON in a code fence despite instructions.
        if text.startswith("```"):
            text = text.strip("`").lstrip("json").strip()
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError):
            raise LLMError(
                LLMError.INVALID_RESPONSE,
                "The AI grading service returned invalid JSON",
            )
        if not isinstance(parsed, dict):
            raise LLMError(
                LLMError.INVALID_RESPONSE,
                "The AI grading service did not return a JSON object",
            )
        return parsed


def _request_hash(request: StructuredRequest) -> str:
    """sha256 over the canonical request — model + messages + schema decide
    the cache key, so a config change never replays a stale response."""
    canonical = json.dumps(
        {
            "task_type": request.task_type,
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
