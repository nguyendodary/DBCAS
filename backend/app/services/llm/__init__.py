"""External LLM integration (Task 3.4 / FR-10, NFR-09).

Public surface kept small: ``LLMService`` + ``build_llm_service`` for
callers, ``ChatMessage``/``StructuredRequest`` DTOs, ``LLMError`` for
normalized failures, ``sanitize_learner_text`` for pre-send redaction.
"""

from .errors import LLMError
from .provider import (
    ChatCompletionsProvider,
    ChatMessage,
    LLMProvider,
    StructuredRequest,
)
from .sanitize import sanitize_learner_text
from .service import CacheStore, LLMService, build_llm_service

__all__ = [
    "LLMError",
    "LLMProvider",
    "LLMService",
    "ChatCompletionsProvider",
    "ChatMessage",
    "StructuredRequest",
    "CacheStore",
    "build_llm_service",
    "sanitize_learner_text",
]
