"""Statistics contracts shared by learner and administrator dashboards."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PointMetric(BaseModel):
    points_earned: Decimal
    points_possible: Decimal
    competency_pct: Decimal | None
    evidence_count: int


class DimensionMetric(PointMetric):
    key: str
    label: str
    rank: int


class CompetencyDimensions(BaseModel):
    overall: PointMetric
    clos: list[DimensionMetric]
    topics: list[DimensionMetric]
    difficulties: list[DimensionMetric]
    clo_mapping_unknown_attempts: int


class ProgressPoint(PointMetric):
    session_id: int
    learner_id: int
    completed_at: datetime


class ScoreBucket(BaseModel):
    lower_bound: int
    upper_bound: int
    upper_inclusive: bool
    count: int


class TopicSuggestion(BaseModel):
    topic: str
    concept_ids: list[int]
    maximum_shortfall_pct: Decimal
    priority: int


class LearnerRank(PointMetric):
    learner_id: int
    rank: int


class OwnRank(BaseModel):
    rank: int | None
    participants: int
    competency_pct: Decimal | None


class StatisticsDashboard(BaseModel):
    learner_id: int | None
    assessment_id: int | None
    dimensions: CompetencyDimensions
    published_formal_sessions: int
    graded_sessions: int
    progress: list[ProgressPoint]
    progress_total: int
    limit: int
    offset: int
    score_distribution: list[ScoreBucket]
    recommendations: list[TopicSuggestion]
    ranking: list[LearnerRank]
