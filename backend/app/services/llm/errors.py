"""Normalized LLM provider errors.

Every failure a provider call can produce is mapped onto one of these codes
so callers never see httpx/vendor specifics. ``http_status`` is the status
DBCAS surfaces to the API layer when the error escapes as an AppError.
"""


class LLMError(Exception):
    """Provider-agnostic failure; ``code`` is stable for callers/tests."""

    NOT_CONFIGURED = "llm_not_configured"
    AUTH_FAILED = "llm_auth_failed"
    RATE_LIMITED = "llm_rate_limited"
    PROVIDER_ERROR = "llm_provider_error"
    TIMEOUT = "llm_timeout"
    UNAVAILABLE = "llm_unavailable"
    INVALID_RESPONSE = "llm_invalid_response"

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_app_error(self):
        from ...errors import AppError

        status = 503
        if self.code == self.INVALID_RESPONSE:
            status = 502
        return AppError(status, self.code, self.message)
