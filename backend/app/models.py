"""SQLAlchemy models for the tables the current backend uses.

db/schema.sql and versioned migrations are the persistence authority. These
models declare the corresponding data-access types and principal constraints;
DDL-only operational indexes are intentional and checked by migration tests.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    ForeignKey,
    CheckConstraint,
    DateTime,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, validates


class Base(DeclarativeBase):
    type_annotation_map = {datetime: DateTime(timezone=True)}


class Role(Base):
    __tablename__ = "role"

    role_id: Mapped[int] = mapped_column(primary_key=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[Optional[str]]


class Account(Base):
    __tablename__ = "account"

    account_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    profile: Mapped[Optional["UserProfile"]] = relationship(back_populates="account")
    roles: Mapped[list[Role]] = relationship(secondary="account_role")
    identities: Mapped[list["AccountIdentity"]] = relationship(back_populates="account")


class AccountIdentity(Base):
    """A linked social sign-in identity (Google/GitHub OAuth).

    One row per (provider, provider_user_id). Links are only written for
    provider-verified emails or for identities the provider returned on a
    completed flow — never on client-supplied data."""

    __tablename__ = "account_identity"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id"),)

    identity_id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    provider: Mapped[str] = mapped_column(String(20))
    provider_user_id: Mapped[str] = mapped_column(String(255))
    provider_email: Mapped[Optional[str]] = mapped_column(String(255))
    email_verified: Mapped[bool] = mapped_column(default=False)
    linked_at: Mapped[datetime] = mapped_column(server_default=func.now())

    account: Mapped[Account] = relationship(back_populates="identities")


class AccountRole(Base):
    __tablename__ = "account_role"

    account_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.role_id"), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserProfile(Base):
    __tablename__ = "user_profile"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"), unique=True)
    full_name: Mapped[str] = mapped_column(String(100))
    student_code: Mapped[Optional[str]] = mapped_column(String(20))
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    date_of_birth: Mapped[Optional[date]]

    account: Mapped[Account] = relationship(back_populates="profile")


class Question(Base):
    __tablename__ = "question"

    question_id: Mapped[int] = mapped_column(primary_key=True)
    question_type: Mapped[str] = mapped_column(String(10))  # 'mcq' | 'sql' | 'essay' (DB CHECK)
    prompt: Mapped[str] = mapped_column(Text)
    reference_answer: Mapped[Optional[str]] = mapped_column(Text)
    difficulty_level: Mapped[int] = mapped_column(SmallInteger, default=1)
    points: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.0"))
    source: Mapped[str] = mapped_column(String(15), default="bank")
    status: Mapped[str] = mapped_column(String(20), default="draft")  # 'draft' | 'validated' | 'retired'
    created_by: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    ai_review: Mapped[Optional[dict]] = mapped_column(JSONB)
    family_id: Mapped[Optional[int]] = mapped_column(ForeignKey("question.question_id"))
    version_no: Mapped[int] = mapped_column(default=1)

    # Official-source provenance + curation metadata (migration 006).
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    source_refs: Mapped[list] = mapped_column(JSONB, default=list)

    @validates("status", "source")
    def canonical_terms(self, key, value):
        return {"rejected": "retired", "ai": "ai_generated"}.get(value, value)

    options: Mapped[list["McqOption"]] = relationship()
    concept_tags: Mapped[list["QuestionConcept"]] = relationship()
    datasets: Mapped[list["SqlTestDataset"]] = relationship(back_populates="question")
    rubrics: Mapped[list["Rubric"]] = relationship(back_populates="question")


class McqOption(Base):
    __tablename__ = "mcq_option"

    option_id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"))
    option_label: Mapped[str] = mapped_column(String(5))
    option_text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(default=False)


class CourseLearningOutcome(Base):
    __tablename__ = "course_learning_outcome"

    clo_id: Mapped[int] = mapped_column(primary_key=True)
    clo_code: Mapped[str] = mapped_column(String(20), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")  # 'active' | 'archived'
    created_by: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    concept_links: Mapped[list["CloConcept"]] = relationship()


class Concept(Base):
    __tablename__ = "concept"
    __table_args__ = (CheckConstraint("difficulty_level BETWEEN 1 AND 5"),)

    concept_id: Mapped[int] = mapped_column(primary_key=True)
    concept_code: Mapped[str] = mapped_column(String(30), unique=True)
    concept_name: Mapped[str] = mapped_column(String(100))
    subject_area: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    difficulty_level: Mapped[int] = mapped_column(SmallInteger, default=1)
    sql_feature: Mapped[Optional[str]] = mapped_column(String(30))


class CloConcept(Base):
    """CLO ↔ concept mapping. ``mapping_source`` 'admin'|'ai' and ``status``
    'pending'|'confirmed'|'rejected' — AI-proposed rows stay pending until an admin
    confirms them (UC06)."""

    __tablename__ = "clo_concept"

    clo_id: Mapped[int] = mapped_column(
        ForeignKey("course_learning_outcome.clo_id"), primary_key=True
    )
    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concept.concept_id"), primary_key=True
    )
    mapping_source: Mapped[str] = mapped_column(String(10), default="admin")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    concept: Mapped["Concept"] = relationship()


class QuestionConcept(Base):
    __tablename__ = "question_concept"

    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.question_id"), primary_key=True
    )
    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concept.concept_id"), primary_key=True
    )
    tag_source: Mapped[str] = mapped_column(String(10), default="admin")
    is_required: Mapped[bool] = mapped_column(default=False)
    confirmed: Mapped[bool] = mapped_column(default=False)
    review_status: Mapped[str] = mapped_column(String(20), default="pending")

    concept: Mapped["Concept"] = relationship()

    @validates("confirmed")
    def align_review_status(self, key, value):
        self.review_status = "confirmed" if value else "pending"
        return value


class ConceptDependency(Base):
    """Directed edge of the prerequisite skill graph: ``concept_id`` depends
    on ``prerequisite_concept_id``. The composite PK blocks duplicate edges;
    self-edges are rejected by the DB CHECK and transitive cycles by the
    service layer."""

    __tablename__ = "concept_dependency"
    __table_args__ = (CheckConstraint("concept_id <> prerequisite_concept_id"),)

    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concept.concept_id"), primary_key=True
    )
    prerequisite_concept_id: Mapped[int] = mapped_column(
        ForeignKey("concept.concept_id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Rubric(Base):
    __tablename__ = "rubric"
    __table_args__ = (CheckConstraint("min_score <= max_score"),)

    rubric_id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"))
    level_name: Mapped[str] = mapped_column(String(30))
    min_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    max_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    criteria: Mapped[str] = mapped_column(Text)

    question: Mapped["Question"] = relationship(back_populates="rubrics")


class SqlTestDataset(Base):
    __tablename__ = "sql_test_dataset"

    dataset_id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"))
    dataset_name: Mapped[str] = mapped_column(String(100))
    setup_sql: Mapped[str] = mapped_column(Text)
    expected_result: Mapped[dict] = mapped_column(JSONB)
    is_edge_case: Mapped[bool] = mapped_column(default=False)

    question: Mapped["Question"] = relationship(back_populates="datasets")


class Assessment(Base):
    __tablename__ = "assessment"

    assessment_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    max_questions: Mapped[int] = mapped_column(SmallInteger, default=13)
    duration_min: Mapped[int] = mapped_column(SmallInteger, default=60)
    target_mcq: Mapped[int] = mapped_column(SmallInteger, default=10)
    target_sql: Mapped[int] = mapped_column(SmallInteger, default=2)
    target_essay: Mapped[int] = mapped_column(SmallInteger, default=1)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # 'draft' | 'published' | 'closed'
    created_by: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    family_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assessment.assessment_id"))
    version_no: Mapped[int] = mapped_column(default=1)

    @validates("status")
    def canonical_status(self, key, value):
        return "published" if value == "active" else value

    targets: Mapped[list["AssessmentConcept"]] = relationship()


class AssessmentConcept(Base):
    __tablename__ = "assessment_concept"

    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessment.assessment_id"), primary_key=True
    )
    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concept.concept_id"), primary_key=True
    )
    min_difficulty: Mapped[int] = mapped_column(SmallInteger, default=1)
    max_difficulty: Mapped[int] = mapped_column(SmallInteger, default=5)
    target_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    concept: Mapped["Concept"] = relationship()


class AssessmentSession(Base):
    __tablename__ = "assessment_session"

    session_id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessment.assessment_id"))
    learner_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    status: Mapped[str] = mapped_column(String(20), default="in_progress")  # 'in_progress' | 'completed' | 'timed_out'
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime]
    submitted_at: Mapped[Optional[datetime]]
    config_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)

    assessment: Mapped[Assessment] = relationship()
    attempts: Mapped[list["Attempt"]] = relationship()


class Attempt(Base):
    """One row per served question. A row is graded iff submitted_at is set."""

    __tablename__ = "attempt"
    __table_args__ = (UniqueConstraint("session_id", "seq_no"),)

    attempt_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("assessment_session.session_id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"))
    seq_no: Mapped[int] = mapped_column(SmallInteger)
    selected_option_id: Mapped[Optional[int]] = mapped_column(ForeignKey("mcq_option.option_id"))
    sql_answer: Mapped[Optional[str]] = mapped_column(Text)
    essay_answer: Mapped[Optional[str]] = mapped_column(Text)
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    grading_detail: Mapped[Optional[dict]] = mapped_column(JSONB)
    served_at: Mapped[datetime] = mapped_column(server_default=func.now())
    submitted_at: Mapped[Optional[datetime]]
    question_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)
    draft_answer: Mapped[Optional[dict]] = mapped_column(JSONB)
    draft_revision: Mapped[int] = mapped_column(default=0)
    draft_saved_at: Mapped[Optional[datetime]]
    submission_hash: Mapped[Optional[str]] = mapped_column(String(64))
    grading_status: Mapped[str] = mapped_column(String(20), default="unsubmitted")

    question: Mapped[Question] = relationship()
    session: Mapped[AssessmentSession] = relationship(back_populates="attempts")


class SelectionLog(Base):
    """One row per adaptive selection decision (FR-15 audit trail)."""

    __tablename__ = "selection_log"
    __table_args__ = (UniqueConstraint("session_id", "seq_no"),)

    log_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_session.session_id")
    )
    seq_no: Mapped[int] = mapped_column(SmallInteger)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"))
    is_fallback: Mapped[bool] = mapped_column(default=False)
    decision_detail: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ConceptCompetency(Base):
    """Per-concept competency result of one session (FR-12/FR-13)."""

    __tablename__ = "concept_competency"
    __table_args__ = (UniqueConstraint("session_id", "concept_id"),)

    competency_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_session.session_id")
    )
    concept_id: Mapped[int] = mapped_column(ForeignKey("concept.concept_id"))
    points_earned: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"))
    points_possible: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"))
    competency_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    below_target: Mapped[bool] = mapped_column(default=False)
    computed_at: Mapped[datetime] = mapped_column(server_default=func.now())

    concept: Mapped["Concept"] = relationship()


class CompetencyGap(Base):
    """A concept flagged below its administrator-set benchmark (FR-14)."""

    __tablename__ = "competency_gap"
    __table_args__ = (UniqueConstraint("session_id", "concept_id"),)

    gap_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_session.session_id")
    )
    concept_id: Mapped[int] = mapped_column(ForeignKey("concept.concept_id"))
    llm_explanation: Mapped[Optional[str]] = mapped_column(Text)
    explanation_context_hash: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="open")  # 'open' | 'reviewed'
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    concept: Mapped["Concept"] = relationship()


class QuestionCandidate(Base):
    """AI-generated draft held OUTSIDE the question bank until an admin
    promotes it (UC10 / NFR-09)."""

    __tablename__ = "question_candidate"

    candidate_id: Mapped[int] = mapped_column(primary_key=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concept.concept_id"))
    question_type: Mapped[str] = mapped_column(String(10))
    payload: Mapped[dict] = mapped_column(JSONB)
    validation_status: Mapped[str] = mapped_column(String(20), default="pending")
    # 'pending' | 'validated' | 'approved' | 'rejected'
    validation_detail: Mapped[Optional[dict]] = mapped_column(JSONB)
    promoted_question_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("question.question_id"), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    concept: Mapped["Concept"] = relationship()


class LlmCache(Base):
    __tablename__ = "llm_cache"

    cache_id: Mapped[int] = mapped_column(primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64), unique=True)
    task_type: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(50))
    response: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class OAuthHandoff(Base):
    __tablename__ = "oauth_handoff"
    jti_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    expires_at: Mapped[datetime]
    consumed_at: Mapped[Optional[datetime]]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class LoginThrottleRecord(Base):
    __tablename__ = "login_throttle"
    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    failures: Mapped[list] = mapped_column(JSONB, default=list)
    expires_at: Mapped[datetime]


class GradingJob(Base):
    __tablename__ = "grading_job"
    __table_args__ = (
        CheckConstraint("status IN ('pending','processing','completed','failed')"),
        CheckConstraint("attempt_count >= 0"),
    )
    job_id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempt.attempt_id"), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    attempt_count: Mapped[int] = mapped_column(default=0)
    available_at: Mapped[datetime] = mapped_column(server_default=func.now())
    lease_until: Mapped[Optional[datetime]]
    last_error_code: Mapped[Optional[str]] = mapped_column(String(80))
    finished_at: Mapped[Optional[datetime]]
