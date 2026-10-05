"""Request/response DTOs for the API layer."""

import re
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

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


class AccountStatusUpdate(BaseModel):
    """UC04 — an admin activates a verified account (or disables one)."""

    status: Literal["active", "disabled"]


# ---------- sessions ----------


class SessionSummary(BaseModel):
    """One of the learner's own sessions — history list and pickers."""

    session_id: int
    assessment_id: int
    assessment_title: str
    status: str  # 'in_progress' | 'completed' | 'timed_out'
    started_at: datetime
    expires_at: datetime
    submitted_at: Optional[datetime] = None
    served_count: int = 0
    answered_count: int = 0


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


# ---------- prerequisite skill graph (Task 5.1) ----------


class SetPrerequisitesRequest(BaseModel):
    """Admin replace of one concept's direct prerequisite set."""

    prerequisite_concept_ids: list[int] = Field(default_factory=list)


class ConceptRef(BaseModel):
    concept_id: int
    concept_code: str
    concept_name: str


class ConceptPrerequisitesResult(BaseModel):
    concept_id: int
    concept_code: str
    concept_name: str
    prerequisites: list[ConceptRef]


class ConceptGraphNode(BaseModel):
    concept_id: int
    concept_code: str
    concept_name: str
    subject_area: str
    prerequisites: list[int] = []  # direct prerequisite concept_ids


class ConceptGraphEdge(BaseModel):
    prerequisite_concept_id: int
    concept_id: int


class ConceptGraphResult(BaseModel):
    nodes: list[ConceptGraphNode]
    edges: list[ConceptGraphEdge]


# ---------- personalized study guidance (Task 5.2) ----------


class GuidancePrerequisiteItem(BaseModel):
    """One direct prerequisite of a recommended concept, with the learner's
    current standing on it."""

    concept_id: int
    concept_code: str
    concept_name: str
    status: str  # 'below_target' | 'satisfied' | 'unassessed'
    competency_pct: Optional[Decimal] = None  # None = no evidence
    target_pct: Optional[Decimal] = None  # None = not an assessment target


class StudyGuidanceItem(BaseModel):
    """One ranked 'study this next' recommendation, fully traceable to
    deterministic factors (benchmark shortfall + prerequisite state)."""

    concept_id: int
    concept_code: str
    concept_name: str
    subject_area: str
    description: Optional[str] = None
    competency_pct: Decimal
    target_pct: Decimal
    shortfall: Decimal  # target_pct - competency_pct (documented rank key)
    priority: int  # 1-based position in the study order
    ready: bool  # False when a direct prerequisite is itself below target
    prerequisites: list[GuidancePrerequisiteItem] = []
    reason: str  # deterministic explanation of the recommendation
    contributing_attempts: list[int] = []
    llm_explanation: Optional[str] = None  # assistive only — never ordered


class StudyGuidanceResult(BaseModel):
    session_id: int
    assessment_id: int
    status: str
    guidance: list[StudyGuidanceItem]


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


# ---------- admin cohort analytics (UC20 / Admin story 9) ----------


class AdminLearnerItem(BaseModel):
    """One learner row in the admin roster — identity plus activity counts."""

    account_id: int
    email: str
    full_name: Optional[str] = None
    sessions_total: int
    sessions_completed: int  # finalized (completed | timed_out)
    last_activity: Optional[datetime] = None


class AdminLearnerSessionsResult(BaseModel):
    """A learner's assessment history for the admin drill-down."""

    account_id: int
    email: str
    full_name: Optional[str] = None
    sessions: list[SessionSummary]


class CohortConceptStat(BaseModel):
    """Cohort-wide standing on one concept.

    Counts are per learner: each learner contributes their latest finalized
    session's competency row for the concept, so repeat sittings cannot skew
    the average or the below-benchmark rate.
    """

    concept_id: int
    concept_code: str
    concept_name: str
    subject_area: str
    learners_assessed: int
    avg_competency_pct: Decimal
    below_target_count: int
    gap_rate_pct: Decimal  # below_target_count / learners_assessed * 100


class CohortOverviewResult(BaseModel):
    """Admin cohort dashboard: who was assessed and where the class is weak."""

    learner_count: int  # learners with >= 1 finalized session
    finalized_sessions: int
    concepts: list[CohortConceptStat]  # all assessed concepts, worst gap first
    weakest_concepts: list[CohortConceptStat]  # top 5 with below_target_count > 0


# ---------- curriculum management (UC05 / Admin story 3) ----------


class ConceptUpsertRequest(BaseModel):
    """Create or fully replace a Core PostgreSQL concept (difficulty 1–5)."""

    concept_code: str = Field(min_length=1, max_length=30)
    concept_name: str = Field(min_length=1, max_length=100)
    subject_area: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    difficulty_level: int = Field(default=1, ge=1, le=5)


class ConceptUpdateRequest(BaseModel):
    concept_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    subject_area: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    difficulty_level: Optional[int] = Field(default=None, ge=1, le=5)


class ConceptDetail(BaseModel):
    concept_id: int
    concept_code: str
    concept_name: str
    subject_area: str
    description: Optional[str] = None
    difficulty_level: int


class CloUpsertRequest(BaseModel):
    clo_code: str = Field(min_length=1, max_length=20)
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None


class CloUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[Literal["active", "archived"]] = None


class CloConceptLink(BaseModel):
    """One clo_concept row as the admin sees it."""

    concept_id: int
    concept_code: str
    concept_name: str
    mapping_source: str  # 'admin' | 'ai'
    status: str  # 'pending' | 'confirmed'


class CloResult(BaseModel):
    clo_id: int
    clo_code: str
    title: str
    description: Optional[str] = None
    status: str
    concepts: list[CloConceptLink] = []


class SetCloConceptsRequest(BaseModel):
    """Admin-confirmed concept set for a CLO (mapping_source='admin',
    status='confirmed'). AI-suggested pending rows are handled by UC06's
    review endpoints, never overwritten silently here."""

    concept_ids: list[int] = Field(default_factory=list)
