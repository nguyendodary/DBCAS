from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    database_url: str = "postgresql://dbcas:change_me@localhost:5432/dbcas"
    jwt_secret: str = "change_me_jwt_secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:5173"]

    # Login throttle (brute-force resistance): per (email, client_ip)
    # invalid-credentials failures allowed inside a sliding window before
    # the endpoint answers 429. Successful login resets the key's window.
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 300

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
    llm_temperature: float = 0.0
    llm_seed: Optional[int] = 42
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2
    llm_backoff_seconds: float = 0.5

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
