"""SQLAlchemy models for the tables the current backend uses.

Column names and constraints mirror db/schema.sql exactly — do not invent
new names here. The DDL in db/schema.sql remains the single source of truth;
these models are a data-access view over it.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Role(Base):
    __tablename__ = "role"

    role_id: Mapped[int] = mapped_column(primary_key=True)
    role_name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[Optional[str]]


class Account(Base):
    __tablename__ = "account"

    account_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    status: Mapped[str] = mapped_column(default="active")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    profile: Mapped[Optional["UserProfile"]] = relationship(back_populates="account")
    roles: Mapped[list[Role]] = relationship(secondary="account_role")


class AccountRole(Base):
    __tablename__ = "account_role"

    account_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.role_id"), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserProfile(Base):
    __tablename__ = "user_profile"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"), unique=True)
    full_name: Mapped[str]
    student_code: Mapped[Optional[str]]
    phone_number: Mapped[Optional[str]]
    date_of_birth: Mapped[Optional[date]]

    account: Mapped[Account] = relationship(back_populates="profile")


class Question(Base):
    __tablename__ = "question"

    question_id: Mapped[int] = mapped_column(primary_key=True)
    question_type: Mapped[str]  # 'mcq' | 'sql' | 'essay' (DB CHECK)
    prompt: Mapped[str] = mapped_column(Text)
    reference_answer: Mapped[Optional[str]] = mapped_column(Text)
    difficulty_level: Mapped[int] = mapped_column(SmallInteger, default=1)
    points: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.0"))
    source: Mapped[str] = mapped_column(default="bank")
    status: Mapped[str] = mapped_column(default="draft")  # 'draft' | 'validated' | 'rejected'
    created_by: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    options: Mapped[list["McqOption"]] = relationship()
    concept_tags: Mapped[list["QuestionConcept"]] = relationship()


class McqOption(Base):
    __tablename__ = "mcq_option"

    option_id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"))
    option_label: Mapped[str]
    option_text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(default=False)


class Concept(Base):
    __tablename__ = "concept"

    concept_id: Mapped[int] = mapped_column(primary_key=True)
    concept_code: Mapped[str] = mapped_column(String(30))
    concept_name: Mapped[str]
    subject_area: Mapped[str]
    description: Mapped[Optional[str]] = mapped_column(Text)
    difficulty_level: Mapped[int] = mapped_column(SmallInteger, default=1)


class QuestionConcept(Base):
    __tablename__ = "question_concept"

    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.question_id"), primary_key=True
    )
    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concept.concept_id"), primary_key=True
    )
    tag_source: Mapped[str] = mapped_column(default="admin")
    is_required: Mapped[bool] = mapped_column(default=False)
    confirmed: Mapped[bool] = mapped_column(default=False)

    concept: Mapped["Concept"] = relationship()


class Rubric(Base):
    __tablename__ = "rubric"

    rubric_id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"))
    level_name: Mapped[str] = mapped_column(String(30))
    min_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    max_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    criteria: Mapped[str] = mapped_column(Text)

    question: Mapped["Question"] = relationship()


class SqlTestDataset(Base):
    __tablename__ = "sql_test_dataset"

    dataset_id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"))
    dataset_name: Mapped[str]
    setup_sql: Mapped[str] = mapped_column(Text)
    expected_result: Mapped[dict] = mapped_column(JSONB)
    is_edge_case: Mapped[bool] = mapped_column(default=False)

    question: Mapped["Question"] = relationship()


class Assessment(Base):
    __tablename__ = "assessment"

    assessment_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[Optional[str]] = mapped_column(Text)
    max_questions: Mapped[int] = mapped_column(SmallInteger, default=13)
    duration_min: Mapped[int] = mapped_column(SmallInteger, default=60)
    target_mcq: Mapped[int] = mapped_column(SmallInteger, default=10)
    target_sql: Mapped[int] = mapped_column(SmallInteger, default=2)
    target_essay: Mapped[int] = mapped_column(SmallInteger, default=1)
    status: Mapped[str] = mapped_column(default="draft")  # 'draft' | 'active' | 'closed'
    created_by: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


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
    status: Mapped[str] = mapped_column(default="in_progress")  # 'in_progress' | 'completed' | 'timed_out'
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime]
    submitted_at: Mapped[Optional[datetime]]

    assessment: Mapped[Assessment] = relationship()
    attempts: Mapped[list["Attempt"]] = relationship()


class Attempt(Base):
    """One row per served question. A row is graded iff submitted_at is set."""

    __tablename__ = "attempt"

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

    question: Mapped[Question] = relationship()
    session: Mapped[AssessmentSession] = relationship(back_populates="attempts")


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
    status: Mapped[str] = mapped_column(default="open")  # 'open' | 'reviewed'
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
