"""Request/response DTOs for the API layer."""

import re
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN_LEN = 8
# bcrypt silently ignores bytes beyond 72 — reject instead of truncating.
PASSWORD_MAX_LEN = 72


def _validate_email(v: str) -> str:
    v = v.strip().lower()
    if not EMAIL_RE.match(v):
        raise ValueError("Invalid email address")
    return v


def _validate_password(v: str) -> str:
    if len(v) < PASSWORD_MIN_LEN:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LEN} characters")
    if len(v.encode("utf-8")) > PASSWORD_MAX_LEN:
        raise ValueError(f"Password must be at most {PASSWORD_MAX_LEN} bytes")
    return v


# ---------- auth ----------

class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str
    password: str
    password_confirm: str

    _email = field_validator("email")(_validate_email)
    _pw = field_validator("password")(_validate_password)

    @field_validator("password_confirm")
    @classmethod
    def _passwords_match(cls, v: str, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Password confirmation does not match")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)

    _email = field_validator("email")(_validate_email)


class AccountSummary(BaseModel):
    account_id: int
    email: str
    full_name: Optional[str] = None
    roles: list[str]
    status: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    account: AccountSummary


class ProvisionAccountRequest(BaseModel):
    """UC04: an Administrator provisions another account (starts disabled)."""

    name: str = Field(min_length=1, max_length=100)
    email: str
    password: str
    role: str = "Administrator"

    _email = field_validator("email")(_validate_email)
    _pw = field_validator("password")(_validate_password)


# ---------- assessment / grading ----------

class SubmitAnswerRequest(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None  # null = unanswered


class AttemptResult(BaseModel):
    attempt_id: int
    session_id: int
    question_id: int
    score: Decimal
    points_possible: Decimal
    is_correct: bool
    submitted_at: datetime


# ---------- SQL sandbox ----------

# Mirrors the configured sandbox limit; also enforced server-side by the
# runner so the schema bound and the executor cannot disagree.
SQL_ANSWER_MAX_LEN = 16000


class RunSqlRequest(BaseModel):
    """UC13 — run (not submit) a learner query on the question's dataset."""

    question_id: int
    sql: str = Field(min_length=1, max_length=SQL_ANSWER_MAX_LEN)


class SqlRunResult(BaseModel):
    """Sanitized sandbox execution result — no container or server details."""

    success: bool
    columns: list[str] = []
    rows: list[list] = []
    row_count: int = 0
    execution_time_ms: int = 0
    error_type: Optional[str] = None
    error_message: Optional[str] = None
