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

# Mirrors the configured sandbox limit; also enforced server-side by the
# sandbox runner (settings.sandbox_max_sql_bytes).
SQL_ANSWER_MAX_LEN = 16000


class SubmitAnswerRequest(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None  # null = unanswered
    sql_answer: Optional[str] = Field(default=None, max_length=SQL_ANSWER_MAX_LEN)
    essay_answer: Optional[str] = Field(default=None, max_length=30000)


class AttemptResult(BaseModel):
    attempt_id: int
    session_id: int
    question_id: int
    score: Decimal
    points_possible: Decimal
    is_correct: bool
    submitted_at: datetime


# ---------- competency (UC16) ----------


class ConceptCompetencyItem(BaseModel):
    """One concept_competency row, decorated for the learner-facing profile."""

    concept_id: int
    concept_code: str
    concept_name: str
    subject_area: str
    points_earned: Decimal
    points_possible: Decimal
    competency_pct: Decimal
    target_pct: Optional[Decimal] = None  # None = not an assessment target
    below_target: bool
    contributing_attempts: list[int] = []  # attempt ids behind the aggregate


class CompetencyProfileResult(BaseModel):
    session_id: int
    assessment_id: int
    status: str
    concepts: list[ConceptCompetencyItem]


# ---------- skill gaps (UC17) ----------


class CompetencyGapItem(BaseModel):
    """One competency_gap row, decorated for the learner-facing report."""

    concept_id: int
    concept_code: str
    concept_name: str
    subject_area: str
    description: Optional[str] = None
    competency_pct: Decimal
    target_pct: Decimal
    gap: Decimal  # shortfall = target_pct - competency_pct (ranking key)
    contributing_attempts: list[int] = []
    status: str  # 'open' | 'reviewed'
    llm_explanation: Optional[str] = None


class CompetencyGapResult(BaseModel):
    """The ranked 'What to study next' list (FR-14): below-benchmark
    concepts ordered by shortfall from target."""

    session_id: int
    assessment_id: int
    status: str
    gaps: list[CompetencyGapItem]


# ---------- SQL sandbox ----------


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
