"""Request/response DTOs for the API layer."""

import re
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

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


# ---------- question bank (UC07 / Admin story 5) ----------


class McqOptionInput(BaseModel):
    option_label: str = Field(min_length=1, max_length=5)
    option_text: str = Field(min_length=1)
    is_correct: bool = False


class SqlDatasetInput(BaseModel):
    dataset_name: str = Field(min_length=1, max_length=100)
    setup_sql: str = Field(min_length=1)
    expected_result: dict  # {"columns": [...], "rows": [[...]]}
    is_edge_case: bool = False


class RubricInput(BaseModel):
    level_name: str = Field(min_length=1, max_length=30)
    min_score: Decimal = Field(ge=0)
    max_score: Decimal = Field(ge=0)
    criteria: str = Field(min_length=1)


class QuestionUpsertRequest(BaseModel):
    """Full question-bank item in one payload — type-specific child
    collections are required/ignored per question_type."""

    question_type: Literal["mcq", "sql", "essay"]
    prompt: str = Field(min_length=1)
    reference_answer: Optional[str] = None
    difficulty_level: int = Field(default=1, ge=1, le=5)
    points: Decimal = Field(gt=0, le=999.99)
    concept_ids: list[int] = Field(default_factory=list)
    required_concept_ids: list[int] = Field(default_factory=list)
    options: list[McqOptionInput] = Field(default_factory=list)
    datasets: list[SqlDatasetInput] = Field(default_factory=list)
    rubrics: list[RubricInput] = Field(default_factory=list)


class QuestionStatusUpdate(BaseModel):
    status: Literal["draft", "validated", "rejected"]


class McqOptionResult(BaseModel):
    option_id: int
    option_label: str
    option_text: str
    is_correct: bool


class SqlDatasetResult(BaseModel):
    dataset_id: int
    dataset_name: str
    setup_sql: str
    expected_result: dict
    is_edge_case: bool


class RubricResult(BaseModel):
    rubric_id: int
    level_name: str
    min_score: Decimal
    max_score: Decimal
    criteria: str


class QuestionConceptTag(BaseModel):
    concept_id: int
    concept_code: str
    concept_name: str
    tag_source: str  # 'admin' | 'ai'
    is_required: bool
    confirmed: bool


class QuestionListItem(BaseModel):
    question_id: int
    question_type: str
    prompt: str
    difficulty_level: int
    points: Decimal
    status: str
    source: str
    updated_at: datetime
    concepts: list[QuestionConceptTag] = []


class QuestionDetail(QuestionListItem):
    reference_answer: Optional[str] = None
    options: list[McqOptionResult] = []
    datasets: list[SqlDatasetResult] = []
    rubrics: list[RubricResult] = []


# ---------- adaptive assessment configuration (UC09 / Admin story 7) ----------


class AssessmentConceptInput(BaseModel):
    concept_id: int
    min_difficulty: int = Field(default=1, ge=1, le=5)
    max_difficulty: int = Field(default=5, ge=1, le=5)
    target_pct: Decimal = Field(ge=0, le=100)

    @model_validator(mode="after")
    def _range_order(self):
        if self.min_difficulty > self.max_difficulty:
            raise ValueError("min_difficulty must be <= max_difficulty")
        return self


class AssessmentUpsertRequest(BaseModel):
    """Adaptive session config: target concepts + difficulty ranges, never
    fixed question sets (the engine picks items at run time)."""

    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    max_questions: int = Field(default=13, ge=1, le=13)
    duration_min: int = Field(default=60, ge=5, le=180)
    target_mcq: int = Field(default=10, ge=0)
    target_sql: int = Field(default=2, ge=0)
    target_essay: int = Field(default=1, ge=0)
    concepts: list[AssessmentConceptInput] = Field(min_length=1)


class AssessmentStatusUpdate(BaseModel):
    status: Literal["draft", "active", "closed"]


class AssessmentConceptResult(BaseModel):
    concept_id: int
    concept_code: str
    concept_name: str
    subject_area: str
    min_difficulty: int
    max_difficulty: int
    target_pct: Decimal


class AssessmentListItem(BaseModel):
    assessment_id: int
    title: str
    status: str  # 'draft' | 'active' | 'closed'
    max_questions: int
    duration_min: int
    created_at: datetime
    target_count: int
    session_count: int


class AssessmentDetail(AssessmentListItem):
    description: Optional[str] = None
    target_mcq: int
    target_sql: int
    target_essay: int
    concepts: list[AssessmentConceptResult] = []


class LearnerAssessmentItem(BaseModel):
    """What a learner sees of an active assessment — no internals."""

    assessment_id: int
    title: str
    description: Optional[str] = None
    duration_min: int
    max_questions: int
    concept_count: int


# ---------- adaptive session engine (UC12 / FR-15) ----------


class ServedMcqOption(BaseModel):
    """An MCQ option as served — the answer key never leaves the server."""

    option_id: int
    option_label: str
    option_text: str


class ServedQuestion(BaseModel):
    """A served question, sanitized for the exam UI.

    ``schema_sql`` (SQL questions only) is the regular dataset's setup DDL
    for the story-4 schema viewer — expected results are never exposed.
    """

    attempt_id: int
    seq_no: int
    question_id: int
    question_type: str  # 'mcq' | 'sql' | 'essay'
    prompt: str
    difficulty_level: int
    points: Decimal
    concepts: list[str] = []
    options: list[ServedMcqOption] = []
    schema_sql: Optional[str] = None
    submitted_at: Optional[datetime] = None
    selected_option_id: Optional[int] = None
    sql_answer: Optional[str] = None
    essay_answer: Optional[str] = None
    score: Optional[Decimal] = None


class SessionStateResult(BaseModel):
    session_id: int
    assessment_id: int
    assessment_title: str
    status: str
    started_at: datetime
    expires_at: datetime
    submitted_at: Optional[datetime] = None
    remaining_seconds: int
    max_questions: int
    served_count: int
    answered_count: int
    current_question: Optional[ServedQuestion] = None
    done: bool  # finalized or max_questions reached


class ServeResult(BaseModel):
    """serve-next response: a pending attempt is returned as-is; ``done``
    means no further question can be served."""

    done: bool
    question: Optional[ServedQuestion] = None


class EvidenceItem(BaseModel):
    """UC18 — one attempt's evidence record for review after finalization."""

    seq_no: int
    attempt_id: int
    question_id: int
    question_type: str
    prompt: str
    difficulty_level: int
    points: Decimal
    concepts: list[ConceptRef] = []
    options: list[McqOptionResult] = []  # correctness revealed post-finalization
    selected_option_id: Optional[int] = None
    sql_answer: Optional[str] = None
    essay_answer: Optional[str] = None
    score: Optional[Decimal] = None
    grading_detail: Optional[dict] = None
    served_at: datetime
    submitted_at: Optional[datetime] = None


class EvidenceResult(BaseModel):
    session_id: int
    status: str
    items: list[EvidenceItem]
