import re
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional
from urllib.parse import unquote, urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from .credential_policy import is_demo_credential

ROOT_DIR = Path(__file__).resolve().parents[2]
OPENROUTER_API_URL = "https://openrouter.ai/api/v1"
OPENROUTER_RELEASE_ENDPOINTS = ("deepinfra/turbo",)
OPENROUTER_ENDPOINT_SLUG = re.compile(r"[a-z0-9][a-z0-9_-]*(?:/[a-z0-9][a-z0-9_-]*){0,3}")


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
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30)
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
    # Demo-only writable role; used only when SANDBOX_WRITABLE is on.
    sandbox_writable_url: str = (
        "postgresql://learner_rw:learner_rw_dev@localhost:5433/postgres"
    )
    sandbox_admin_url: str = (
        "postgresql://postgres:change_me_sandbox@localhost:5433/postgres"
    )
    sandbox_learner_role: str = "learner_ro"
    sandbox_statement_timeout_ms: int = Field(default=3000, ge=1, le=3000)
    sandbox_max_rows: int = 1000
    sandbox_max_sql_bytes: int = 16000
    sandbox_max_result_bytes: int = Field(default=262144, ge=1024, le=1048576)
    sandbox_max_cell_bytes: int = Field(default=16384, ge=256, le=65536)
    sandbox_max_setup_bytes: int = 65536
    sandbox_connect_timeout_seconds: int = 5
    sandbox_mode: Literal["shared", "ephemeral"] = "shared"
    sandbox_container_image: str = Field(default="dbcas-sql-ephemeral:local", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._/:@-]+$")
    sandbox_container_lifetime_seconds: int = Field(default=45, ge=10, le=90)

    # Multi-statement SQL sandbox capability flags. All DEFAULT OFF so an
    # unchanged deployment keeps the exact legacy single-SELECT behavior.
    # Environment names match the field names uppercased:
    #   SANDBOX_MULTI_STATEMENT, SANDBOX_WRITABLE, GRADING_STATE_MODE.
    sandbox_multi_statement: bool = False
    sandbox_writable: bool = False
    grading_state_mode: bool = False
    # Script-level budgets (used only when SANDBOX_MULTI_STATEMENT is on).
    sandbox_max_statements: int = Field(default=32, ge=1, le=128)
    sandbox_max_script_ms: int = Field(default=5000, ge=1, le=30000)
    sandbox_max_rows_per_script: int = Field(default=2000, ge=1)
    sandbox_max_result_bytes_per_script: int = Field(default=524288, ge=1024, le=2097152)

    # PR-B1 broker skeleton. The five defaults below are approved by the owner
    # (2026-11-21, docs/analysis/owner-decisions.md). Flag SANDBOX_BROKER is
    # OFF by default (the sheet's BROKER_ENABLED is superseded); with it OFF no
    # existing runtime path changes. Real execution is B2, not B1.
    sandbox_broker: bool = False
    sandbox_broker_channel: Literal["unix", "mtls"] = "unix"
    sandbox_broker_socket_path: str = "/run/dbcas/broker.sock"
    sandbox_broker_peer_identity: str = "dbcas-api"
    sandbox_broker_issuer_id: str = "dbcas-broker-local"
    sandbox_broker_issuer_key: str = ""
    # Owner-approved TTL: 300 s.
    sandbox_broker_capability_ttl_seconds: int = Field(default=300, ge=30, le=900)
    sandbox_broker_schema_version: int = 1
    sandbox_broker_dataset_digests: dict[str, str] = Field(default_factory=dict)
    sandbox_broker_allowed_images: dict[str, str] = Field(default_factory=dict)
    sandbox_broker_template: dict[str, object] = Field(default_factory=lambda: {
        "network": "none", "read_only_root": True, "uid": 10001, "gid": 10001,
        "cap_drop": ["ALL"], "no_new_privileges": True, "pids_limit": 128,
        "memory_mb": 256, "cpus": 1,
    })
    # Owner-approved audit: SQL text is never stored; retention is 30 days.
    sandbox_broker_audit_retention_days: int = Field(default=30, ge=1, le=365)
    sandbox_broker_client_cert_path: str = ""
    sandbox_broker_client_key_path: str = ""
    sandbox_broker_ca_cert_path: str = ""
    # PR-B2 execution slice. OFF by default; "stub" never runs real SQL.
    sandbox_broker_runtime: Literal["stub", "docker"] = "stub"
    sandbox_broker_image_digest: str = ""
    sandbox_broker_queue_size: int = Field(default=8, ge=1, le=64)
    sandbox_broker_admission_timeout_ms: int = Field(default=5000, ge=100, le=30000)

    # Social sign-in (OAuth 2.0 authorization-code flow, backend-managed).
    # Empty client id = provider disabled; /auth/oauth/{provider}/start then
    # answers 503 oauth_not_configured; the SPA retains a safe email notice.
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

    # Self-service password recovery (services/password_reset.py). SMTP is
    # optional: when SMTP_HOST or SMTP_FROM is empty the reset endpoints
    # answer password_reset_unavailable and every other auth flow is
    # unaffected. Development uses the `mailpit` compose service
    # (127.0.0.1:1026 SMTP / 127.0.0.1:8026 UI); production must configure
    # a real relay.
    smtp_host: str = ""
    smtp_port: int = Field(default=1026, ge=1, le=65535)
    smtp_from: str = ""
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_starttls: bool = False
    smtp_ssl: bool = False
    smtp_timeout_seconds: float = Field(default=10, ge=1, le=60)
    password_reset_token_ttl_minutes: int = Field(default=15, ge=1, le=120)
    # Every request counts against the window (not only failures).
    password_reset_rate_limit_attempts: int = Field(default=5, ge=1)
    password_reset_ip_rate_limit_attempts: int = Field(default=20, ge=1)
    password_reset_confirm_rate_limit_attempts: int = Field(default=10, ge=1)
    password_reset_rate_limit_window_seconds: int = Field(default=900, ge=60)

    # External LLM provider (Task 3.4). Any OpenAI-compatible
    # chat-completions endpoint works; empty key = AI features disabled
    # gracefully (llm_not_configured), the rest of the app unaffected.
    llm_provider: Literal["compatible", "openrouter"] = "compatible"
    llm_api_key: str = Field(default="", repr=False)
    llm_base_url: str = ""
    llm_model: str = ""
    openrouter_api_key: str = Field(default="", repr=False)
    openrouter_base_url: str = OPENROUTER_API_URL
    openrouter_model: str = ""
    openrouter_http_referer: str = ""
    openrouter_app_title: str = ""
    openrouter_data_collection: Literal["deny", "allow"] = "deny"
    openrouter_zdr: bool = True
    openrouter_provider_endpoint: str = ""
    llm_temperature: float = 0.1
    llm_seed: Optional[int] = 42
    llm_timeout_seconds: float = Field(default=90.0, ge=1, le=120, allow_inf_nan=False)
    llm_max_retries: int = Field(default=2, ge=0, le=3)
    llm_backoff_seconds: float = Field(default=0.5, ge=0, le=10, allow_inf_nan=False)
    llm_prompt_version: str = "2026-10-11-v1"
    # Separate opt-in: existing grading credentials do not enable translation.
    question_translation_enabled: bool = False
    grading_job_max_attempts: int = 3
    auto_grade_essays: bool = False
    grading_job_retry_seconds: int = 30
    session_sweep_seconds: int = 5
    # FIXED-paper tab-leave guard. The server owns both values: a reported
    # leave shorter than the grace period is ignored, and the third counted
    # violation cancels the attempt with zero points.
    tab_leave_grace_seconds: int = Field(default=3, ge=1, le=60)
    tab_leave_violation_limit: int = Field(default=3, ge=1, le=10)
    # Tolerated for environment compatibility; the prompt builder is template-only.
    prompt_builder_model_path: str = ""
    prompt_builder_timeout_seconds: int = Field(default=8, ge=1, le=30)
    evaluation_fake_delay_seconds: float = Field(default=0, ge=0, le=15)
    evaluation_fake_error: bool = False
    evaluation_debounce_seconds: float = Field(default=3, ge=0, le=30, allow_inf_nan=False)
    practice_preview_rate_limit_attempts: int = Field(default=30, ge=1, le=1000)
    practice_preview_rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_connect_timeout_seconds: int = Field(default=5, ge=2, le=30)
    database_pool_timeout_seconds: int = Field(default=5, ge=1, le=30)
    readiness_database_timeout_seconds: int = Field(default=2, ge=2, le=10)

    @model_validator(mode="after")
    def _configure_openrouter(self):
        if self.llm_provider != "openrouter":
            if self.deployment_mode != "development":
                host = (urlsplit(self.llm_base_url).hostname or "").rstrip(".")
                if host == "openrouter.ai" or host.endswith(".openrouter.ai"):
                    raise ValueError("OpenRouter in staging/production requires LLM_PROVIDER=openrouter")
            return self
        if not self.openrouter_api_key.strip():
            raise ValueError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter")
        model = self.openrouter_model.strip()
        if not model or len(model) > 80:
            raise ValueError("OPENROUTER_MODEL must contain 1–80 characters when LLM_PROVIDER=openrouter")
        base_url = self.openrouter_base_url.strip()
        try:
            endpoint = urlsplit(base_url)
            valid_url = (endpoint.scheme == "https" and endpoint.hostname and endpoint.username is None
                         and not endpoint.query and not endpoint.fragment)
        except ValueError:
            valid_url = False
        if not valid_url:
            raise ValueError("OPENROUTER_BASE_URL must be an HTTPS URL without credentials, query or fragment")
        route = self.openrouter_provider_endpoint.strip()
        if route and not OPENROUTER_ENDPOINT_SLUG.fullmatch(route):
            raise ValueError("OPENROUTER_PROVIDER_ENDPOINT must be one OpenRouter endpoint slug")
        if self.deployment_mode != "development":
            if base_url.rstrip("/") != OPENROUTER_API_URL:
                raise ValueError("Staging/production requires the official OPENROUTER_BASE_URL")
            if "/" not in model or model.lower().startswith("openrouter/"):
                raise ValueError("Staging/production requires a concrete OPENROUTER_MODEL")
            if self.openrouter_data_collection != "deny" or not self.openrouter_zdr:
                raise ValueError("Staging/production requires OPENROUTER_DATA_COLLECTION=deny and OPENROUTER_ZDR=true")
            if route not in OPENROUTER_RELEASE_ENDPOINTS:
                approved = ", ".join(OPENROUTER_RELEASE_ENDPOINTS)
                raise ValueError(
                    "Staging/production requires OPENROUTER_PROVIDER_ENDPOINT to be an approved "
                    f"provider/variant identifier ({approved})"
                )
        for name in ("openrouter_http_referer", "openrouter_app_title"):
            value = getattr(self, name)
            if any(not 32 <= ord(char) <= 126 for char in value):
                raise ValueError(f"{name.upper()} must use printable ASCII for HTTP headers")
        # Keep auto-grading, translation and prompt audit on the same effective configuration.
        self.llm_api_key = self.openrouter_api_key.strip()
        self.llm_base_url = base_url
        self.llm_model = model
        self.openrouter_provider_endpoint = route
        return self

    @model_validator(mode="after")
    def _deployment_safety(self):
        # Report key names only: configuration errors must never disclose values.
        if self.sandbox_writable and self.sandbox_mode != "ephemeral":
            raise ValueError(
                "SANDBOX_WRITABLE requires SANDBOX_MODE=ephemeral in every deployment mode"
            )
        if self.deployment_mode == "development":
            return self
        for key in ('jwt_secret', 'smtp_password', 'google_client_secret', 'github_client_secret', 'llm_api_key'):
            value = getattr(self, key)
            if value and is_demo_credential(value):
                raise ValueError(f"Unsafe {key.upper()}: known demo credentials are forbidden outside development")
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
            if (is_demo_credential(password) or len(password) < 16 or password.lower() in defaults
                    or any(s in password.lower() for s in unsafe)):
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
        # Writable learner SQL is a per-execution container boundary outside
        # development. Fail closed at startup — never silently fall back to
        # the shared sandbox or grant the API new Docker privileges.
        if self.smtp_host.strip().lower() == "mailpit":
            raise ValueError("SMTP_HOST must not be the development Mailpit service outside development")
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
