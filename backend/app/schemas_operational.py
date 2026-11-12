"""Public response contracts for practice processing and operational routes."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from .services.prompt_builder import Evaluation


class StatusResult(BaseModel):
    status: str


class PingResult(BaseModel):
    message: Literal["pong"]


class DependencyStatus(BaseModel):
    database: bool
    sandbox: bool


class ReadinessResult(BaseModel):
    status: Literal["ready", "not_ready"]
    dependencies: DependencyStatus


class CapabilityResult(BaseModel):
    available: bool


class ProviderStatus(BaseModel):
    name: Literal["google", "github"]
    configured: bool


class OAuthProvidersResult(BaseModel):
    providers: list[ProviderStatus]


class SystemStatus(BaseModel):
    evaluator_configured: bool
    prompt_builder_configured: bool
    fallback_available: bool
    mode: Literal["local"]
    database: str
    pipeline: str


class EvaluationMetric(BaseModel):
    earned: str
    possible: str
    percentage: float


class EvaluationDimension(EvaluationMetric):
    label: str


class EvaluationHistory(EvaluationMetric):
    session_id: int
    ordinal: int
    date: str


class PipelineResult(BaseModel):
    evaluation: Evaluation
    prompt_hash: str
    builder_fallback: bool
    evaluator_fallback: bool


class ConceptResult(BaseModel):
    concept_id: int
    concept_code: str | None = None
    concept_name: str | None = None
    competency_pct: float | None = None
    target_pct: float | None = None
    below_target: bool = False
    covered: bool = True
    strength: str | None = None
    weakness: str | None = None
    recommendation: str | None = None


class QuestionResult(BaseModel):
    attempt_id: int
    question_id: int
    question_type: str
    prompt: str
    score: float | None
    points: float
    grading_status: str


class EvaluationView(BaseModel):
    status: Literal["empty", "pending", "processing", "updating", "provisional", "ready", "failed"]
    provisional: bool = False
    final: bool = False
    attempt_count: int
    pending_count: int
    dimensions: dict[Literal["clo", "topic", "difficulty"], list[EvaluationDimension]]
    history: list[EvaluationHistory]
    score: EvaluationMetric | None
    details_truncated: bool
    input_hash: str
    result: PipelineResult | None
    approved: bool
    adjusted: bool
    source: Literal["ai", "admin_approved", "legacy_admin_approved"] | None = None
    approved_at: datetime | None = None
    uncovered_concepts: list[dict[str, Any]] = []
    question_results: list[QuestionResult] = []
    concept_results: list[ConceptResult] = []


class AwaitingApproval(BaseModel):
    status: Literal["awaiting_approval"]
    message: str


class GradingSummary(BaseModel):
    session_id: int
    learner_id: int
    learner_name: str | None
    assessment_title: str
    release_status: str
    result_release_policy: Literal["IMMEDIATE", "HUMAN_VERIFIED"]
    submitted_at: datetime | None
    revision: int


class ReviewedOption(BaseModel):
    option_id: int
    option_text: str
    is_correct: bool


class ReviewedRubric(BaseModel):
    level_name: str
    min_score: float
    max_score: float
    criteria: str


class GradeDecision(BaseModel):
    reviewer_id: int
    reviewed_at: datetime
    comments: str | None
    approved_score: float


class GradingItem(BaseModel):
    attempt_id: int
    question_id: int
    question_type: Literal["mcq", "sql", "essay"]
    prompt: str
    reference_answer: str | None
    points: float
    selected_option_id: int | None
    options: list[ReviewedOption]
    sql_answer: str | None
    essay_answer: str | None
    submitted_at: datetime | None
    grading_status: str
    automated_score: float | None
    automated_detail: dict[str, Any] | None
    final_score: float | None
    revision: int
    review: GradeDecision | None
    rubrics: list[ReviewedRubric]


class ScoreEdit(BaseModel):
    attempt_id: int
    reviewer_id: int
    old_score: float | None
    new_score: float
    reason: str
    created_at: datetime


class ReleaseEvent(BaseModel):
    previous_status: str | None
    new_status: str
    reviewer_id: int | None
    created_at: datetime


class GradingDetail(GradingSummary):
    items: list[GradingItem]
    learner_defined: bool
    evaluation: PipelineResult | None
    final_result: dict[str, Any] | None = None
    concept_results: list[dict[str, Any]] = []
    score_edits: list[ScoreEdit]
    manual_review_required: bool
    events: list[ReleaseEvent]
