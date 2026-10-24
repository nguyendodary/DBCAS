from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional
from urllib.parse import unquote, urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env", extra="ignore", hide_input_in_errors=True
    )

    deployment_mode: Literal["development", "staging", "production"] = "development"

    database_url: str = "postgresql://dbcas:change_me@localhost:5432/dbcas"
    jwt_secret: str = "change_me_jwt_secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, ge=1, le=480)
    access_session_max_minutes: int = Field(default=480, ge=60, le=1440)
    cors_origins: list[str] = ["http://localhost:5173"]

    # Login throttle (brute-force resistance): per (email, client_ip)
    # invalid-credentials failures allowed inside a sliding window before
    # the endpoint answers 429. Successful login resets the key's window.
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 300
    login_rate_limit_max_keys: int = 10_000

    # SQL sandbox (docker compose service: sandbox). learner_ro is the
    # read-only role created by sandbox/init; the admin URL is used only to
    # provision and drop per-execution dataset schemas — never for learner SQL.
    sandbox_url: str = (
        "postgresql://learner_ro:learner_ro_dev@localhost:5433/postgres"
    )
    sandbox_admin_url: str = (
        "postgresql://postgres:change_me_sandbox@localhost:5433/postgres"
    )
    sandbox_learner_role: str = "learner_ro"
    sandbox_statement_timeout_ms: int = 3000
    sandbox_max_rows: int = 1000
    sandbox_max_sql_bytes: int = 16000
    sandbox_max_result_bytes: int = Field(default=262144, ge=1024, le=1048576)
    sandbox_max_cell_bytes: int = Field(default=16384, ge=256, le=65536)
    sandbox_max_setup_bytes: int = 65536
    sandbox_connect_timeout_seconds: int = 5

    # Social sign-in (OAuth 2.0 authorization-code flow, backend-managed).
    # Empty client id = provider disabled; /auth/oauth/{provider}/start then
    # answers 503 oauth_not_configured and the SPA disables the button.
    # The SPA origin must serve /api/* to this backend (vite proxy in dev,
    # same-origin reverse proxy in production) because the OAuth state and
    # handoff cookies are scoped to it.
    frontend_url: str = "http://localhost:5173"
    oauth_state_ttl_seconds: int = 600
    oauth_handoff_ttl_seconds: int = 120
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = (
        "http://localhost:5173/api/v1/auth/oauth/google/callback"
    )
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = (
        "http://localhost:5173/api/v1/auth/oauth/github/callback"
    )

    # External LLM provider (Task 3.4). Any OpenAI-compatible
    # chat-completions endpoint works; empty key = AI features disabled
    # gracefully (llm_not_configured), the rest of the app unaffected.
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    llm_temperature: float = 0.1
    llm_seed: Optional[int] = 42
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2
    llm_backoff_seconds: float = 0.5
    llm_prompt_version: str = "2026-10-11-v1"
    # Separate opt-in: existing grading credentials do not enable translation.
    question_translation_enabled: bool = False
    grading_job_max_attempts: int = 3
    grading_job_retry_seconds: int = 30
    session_sweep_seconds: int = 5
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_connect_timeout_seconds: int = Field(default=5, ge=2, le=30)
    database_pool_timeout_seconds: int = Field(default=5, ge=1, le=30)
    readiness_database_timeout_seconds: int = Field(default=2, ge=2, le=10)

    @model_validator(mode="after")
    def _deployment_safety(self):
        # Report key names only: configuration errors must never disclose values.
        if self.deployment_mode == "development":
            return self
        unsafe = ("change", "replace", "placeholder", "example", "your-", "test-secret")
        secret = self.jwt_secret.strip()
        if len(secret.encode()) < 32 or any(s in secret.lower() for s in unsafe):
            raise ValueError("Unsafe JWT_SECRET: staging/production requires a random secret of at least 32 bytes")
        if self.jwt_algorithm != "HS256":
            raise ValueError("JWT_ALGORITHM must be HS256 for the configured symmetric key")
        defaults = {"postgres", "password", "test", "dbcas_dev", "learner_ro_dev", "changeme"}
        endpoints = []
        for key in ("database_url", "sandbox_url", "sandbox_admin_url"):
            parsed = urlsplit(getattr(self, key))
            password = unquote(parsed.password or "")
            if len(password) < 16 or password.lower() in defaults or any(s in password.lower() for s in unsafe):
                raise ValueError(f"Unsafe {key.upper()}: configure a distinct non-default database password")
            endpoints.append((parsed.hostname, parsed.port or 5432))
        if endpoints[0] in endpoints[1:]:
            raise ValueError("Sandbox and application database must be on distinct PostgreSQL servers")
        if not self.frontend_url.startswith("https://") or any(
            not origin.startswith("https://") or "*" in origin for origin in self.cors_origins
        ):
            raise ValueError("Staging/production requires HTTPS FRONTEND_URL and explicit HTTPS CORS_ORIGINS")
        if not 1 <= self.sandbox_statement_timeout_ms <= 3000:
            raise ValueError("SANDBOX_STATEMENT_TIMEOUT_MS must be at most 3000")
        return self

    @field_validator("database_url")
    @classmethod
    def _use_psycopg3(cls, v: str) -> str:
        # schema.sql/database use the plain postgresql:// scheme; SQLAlchemy
        # needs the explicit psycopg v3 driver name.
        if v.startswith("postgresql://"):
            return "postgresql+psycopg://" + v[len("postgresql://"):]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
