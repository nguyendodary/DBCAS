"""SQLAlchemy models for the tables the current backend uses.

db/schema.sql and versioned migrations are the persistence authority. These
models declare the corresponding data-access types and principal constraints;
DDL-only operational indexes are intentional and checked by migration tests.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    ForeignKeyConstraint,
    CheckConstraint,
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
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
    # False only for OAuth-provisioned accounts whose hash is an unusable
    # random value; setting/resetting a real password flips it to True.
    password_set: Mapped[bool] = mapped_column(default=True, server_default="true")
    password_changed_at: Mapped[Optional[datetime]]
    status: Mapped[str] = mapped_column(String(20), default="active")
    # Separate capability: Administrator alone never implies authority to
    # grant or revoke administrative roles.
    can_manage_roles: Mapped[bool] = mapped_column(default=False, server_default="false")
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


class AccountRoleAudit(Base):
    """Append-only record of account role changes and trusted bootstrap."""

    __tablename__ = "account_role_audit"
    __table_args__ = (
        CheckConstraint(
            "(action_type IN ('ROLE_GRANTED', 'ROLE_REVOKED') "
            "AND actor_account_id IS NOT NULL AND previous_role IS NOT NULL "
            "AND new_role IS NOT NULL AND previous_role <> new_role) OR "
            "(action_type = 'ROLE_MANAGER_BOOTSTRAPPED' "
            "AND actor_account_id IS NULL AND previous_role IS NULL AND new_role IS NULL)"
        ),
    )

    audit_id: Mapped[int] = mapped_column(primary_key=True)
    action_type: Mapped[str] = mapped_column(String(40))
    actor_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))
    target_account_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    previous_role: Mapped[Optional[str]] = mapped_column(String(50))
    new_role: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


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
    __table_args__ = (CheckConstraint("original_locale IN ('en', 'vi')"),)

    question_id: Mapped[int] = mapped_column(primary_key=True)
    question_type: Mapped[str] = mapped_column(String(10))  # 'mcq' | 'sql' | 'essay' (DB CHECK)
    prompt: Mapped[str] = mapped_column(Text)
    original_locale: Mapped[str] = mapped_column(String(16), default="en", server_default="en")
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

    options: Mapped[list["McqOption"]] = relationship(order_by="McqOption.option_id")
    translations: Mapped[list["QuestionTranslation"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    concept_tags: Mapped[list["QuestionConcept"]] = relationship()
    datasets: Mapped[list["SqlTestDataset"]] = relationship(back_populates="question")
    rubrics: Mapped[list["Rubric"]] = relationship(
        back_populates="question", order_by="Rubric.rubric_id"
    )


class McqOption(Base):
    __tablename__ = "mcq_option"

    option_id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"))
    option_label: Mapped[str] = mapped_column(String(5))
    option_text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(default=False)


class QuestionTranslation(Base):
    """Locale-specific learner prose; technical and scoring data stay canonical."""

    __tablename__ = "question_translation"
    __table_args__ = (
        CheckConstraint("locale ~ '^[a-z]{2}(-[A-Z]{2})?$'"),
        CheckConstraint("jsonb_typeof(option_texts) = 'object'"),
        CheckConstraint("jsonb_typeof(rubrics) = 'object'"),
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.question_id", ondelete="CASCADE"), primary_key=True
    )
    locale: Mapped[str] = mapped_column(String(16), primary_key=True)
    source_hash: Mapped[str] = mapped_column(String(64))
    prompt: Mapped[str] = mapped_column(Text)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    option_texts: Mapped[dict] = mapped_column(JSONB, default=dict)
    rubrics: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    question: Mapped["Question"] = relationship(back_populates="translations")


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
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    learning_objectives: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)


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


class QuestionClo(Base):
    """Direct CLO assignment or AI proposal for a question.

    ``tag_source`` is 'admin' for an administrator decision, 'auto' for the
    deterministic single-reachable-CLO rule, and 'ai' for a pending model
    proposal. AI rows never become effective until reviewed. The partial
    unique index allows at most one non-rejected primary CLO per question.
    """

    __tablename__ = "question_clo"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'rejected')",
            name="question_clo_status_check",
        ),
        CheckConstraint(
            "tag_source IN ('admin', 'auto', 'ai')",
            name="question_clo_source_check",
        ),
        Index(
            "question_clo_primary_idx",
            "question_id",
            unique=True,
            postgresql_where=text("is_primary AND status <> 'rejected'"),
        ),
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.question_id"), primary_key=True
    )
    clo_id: Mapped[int] = mapped_column(
        ForeignKey("course_learning_outcome.clo_id"), primary_key=True
    )
    is_primary: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    tag_source: Mapped[str] = mapped_column(String(10), default="admin")
    confirmed_at: Mapped[Optional[datetime]]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class CourseDocument(Base):
    """Admin-supplied course material (migration 023).

    The upload is never persisted: only the normalized extracted text, its
    SHA-256 digest and page/heading metadata are stored. Documents stay
    invisible outside the administrator surface and are only usable for
    grounded generation after ``status='approved'``.
    """

    __tablename__ = "course_document"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'approved', 'archived')",
            name="course_document_status_check",
        ),
        CheckConstraint("source_type IN ('upload')", name="course_document_source_check"),
        CheckConstraint("sha256 ~ '^[a-f0-9]{64}$'", name="course_document_sha256_check"),
        CheckConstraint(
            "char_count >= 1 AND (page_count IS NULL OR page_count >= 1)",
            name="course_document_counts_check",
        ),
    )

    document_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    source_type: Mapped[str] = mapped_column(String(20), default="upload", server_default="upload")
    mime_type: Mapped[str] = mapped_column(String(100))
    original_filename: Mapped[Optional[str]] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64))
    char_count: Mapped[int]
    page_count: Mapped[Optional[int]]
    status: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft")
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now())
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))
    approved_at: Mapped[Optional[datetime]]
    text_policy_version: Mapped[str] = mapped_column(
        String(20), default="untrusted-v1", server_default="untrusted-v1"
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        order_by="DocumentChunk.ordinal", cascade="all, delete-orphan"
    )
    clo_links: Mapped[list["DocumentClo"]] = relationship(cascade="all, delete-orphan")


class DocumentChunk(Base):
    """One bounded, ordered passage of a course document's extracted text."""

    __tablename__ = "document_chunk"
    __table_args__ = (
        UniqueConstraint("document_id", "ordinal", name="document_chunk_document_ordinal_key"),
        CheckConstraint("ordinal >= 1", name="document_chunk_ordinal_check"),
        CheckConstraint(
            "(page_from IS NULL OR page_from >= 1) "
            "AND (page_to IS NULL OR page_from IS NULL OR page_to >= page_from)",
            name="document_chunk_pages_check",
        ),
        CheckConstraint("length(text) >= 1", name="document_chunk_text_check"),
        CheckConstraint("char_count = length(text)", name="document_chunk_chars_check"),
        CheckConstraint("text_hash ~ '^[a-f0-9]{64}$'", name="document_chunk_hash_check"),
    )

    chunk_id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("course_document.document_id", ondelete="CASCADE")
    )
    ordinal: Mapped[int]
    page_from: Mapped[Optional[int]]
    page_to: Mapped[Optional[int]]
    heading: Mapped[Optional[str]] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(String(64))
    char_count: Mapped[int]


class DocumentClo(Base):
    """Attachment of a document to an active course learning outcome."""

    __tablename__ = "document_clo"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="document_clo_status_check",
        ),
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("course_document.document_id", ondelete="CASCADE"), primary_key=True
    )
    clo_id: Mapped[int] = mapped_column(
        ForeignKey("course_learning_outcome.clo_id"), primary_key=True
    )
    status: Mapped[str] = mapped_column(String(20), default="approved", server_default="approved")
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))
    approved_at: Mapped[Optional[datetime]]

    clo: Mapped["CourseLearningOutcome"] = relationship()


class QuestionEvidence(Base):
    """Exact quoted passage supporting an approved question (migration 023)."""

    __tablename__ = "question_evidence"
    __table_args__ = (
        CheckConstraint("length(quote) >= 1", name="question_evidence_quote_check"),
        CheckConstraint(
            "(start_offset IS NULL OR start_offset >= 0) "
            "AND (end_offset IS NULL OR start_offset IS NULL OR end_offset >= start_offset)",
            name="question_evidence_offsets_check",
        ),
        CheckConstraint("source_hash ~ '^[a-f0-9]{64}$'", name="question_evidence_hash_check"),
    )

    evidence_id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.question_id", ondelete="CASCADE")
    )
    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunk.chunk_id"))
    quote: Mapped[str] = mapped_column(Text)
    start_offset: Mapped[Optional[int]]
    end_offset: Mapped[Optional[int]]
    source_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


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
    result_release_policy: Mapped[str] = mapped_column(String(20), default="HUMAN_VERIFIED")

    @validates("status")
    def canonical_status(self, key, value):
        return "published" if value == "active" else value

    targets: Mapped[list["AssessmentConcept"]] = relationship()
    # DB-level ON DELETE CASCADE never removes a version referenced by a
    # session: session FKs block assessment deletion while sessions exist.
    blueprints: Mapped[list["AssessmentBlueprint"]] = relationship(
        passive_deletes=True
    )


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


class AssessmentBlueprint(Base):
    """Immutable, versioned evidence mix for one assessment competency band."""

    __tablename__ = "assessment_blueprint"
    __table_args__ = (
        CheckConstraint("difficulty_band IN ('EASY', 'MEDIUM', 'HARD')"),
        CheckConstraint("status IN ('approved', 'retired')"),
        CheckConstraint("target_mcq + target_sql + target_essay = max_questions"),
        UniqueConstraint("assessment_id", "subject_area", "difficulty_band", "version_no"),
    )

    blueprint_id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey(
        "assessment.assessment_id", ondelete="CASCADE"))
    subject_area: Mapped[str] = mapped_column(String(100))
    difficulty_band: Mapped[str] = mapped_column(String(10))
    version_no: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(20), default="approved")
    max_questions: Mapped[int] = mapped_column(SmallInteger)
    target_mcq: Mapped[int] = mapped_column(SmallInteger)
    target_sql: Mapped[int] = mapped_column(SmallInteger)
    target_essay: Mapped[int] = mapped_column(SmallInteger)
    scoring: Mapped[dict] = mapped_column(JSONB, default=dict)
    evidence_types: Mapped[list] = mapped_column(JSONB, default=list)
    approval_basis: Mapped[str] = mapped_column(Text)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))
    approved_at: Mapped[datetime] = mapped_column(server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class AssessmentSession(Base):
    __tablename__ = "assessment_session"
    __table_args__ = (CheckConstraint("locale ~ '^[a-z]{2}(-[A-Z]{2})?$'"),
                      CheckConstraint("purpose IN ('TEST', 'PRACTICE')"),
                      CheckConstraint("purpose_source IN ('SERVER', 'BACKFILL')"),
                      UniqueConstraint("session_id", "learner_id", name="session_owner_unique"))

    session_id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assessment.assessment_id"))
    learner_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    # 'in_progress' | 'completed' | 'timed_out' | 'cancelled'
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    # Server-owned TEST/PRACTICE; purpose_source marks server-created vs
    # deterministic migration backfill. Only SERVER TEST rows count toward
    # cumulative competency.
    purpose: Mapped[str] = mapped_column(String(10), default="PRACTICE", server_default="PRACTICE")
    purpose_source: Mapped[str] = mapped_column(String(10), default="SERVER", server_default="SERVER")
    locale: Mapped[str] = mapped_column(String(16), default="en")
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime]
    submitted_at: Mapped[Optional[datetime]]
    config_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)
    result_release_policy: Mapped[str] = mapped_column(String(20), default="HUMAN_VERIFIED")
    release_status: Mapped[str] = mapped_column(String(20), default="unsubmitted")
    start_request_id: Mapped[Optional[str]] = mapped_column(String(36))
    blueprint_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("assessment_blueprint.blueprint_id")
    )
    review_revision: Mapped[int] = mapped_column(default=0)
    published_at: Mapped[Optional[datetime]]
    tab_leave_count: Mapped[int] = mapped_column(default=0, server_default="0")
    cancelled_at: Mapped[Optional[datetime]]
    cancel_reason: Mapped[Optional[str]] = mapped_column(String(40))

    assessment: Mapped[Optional[Assessment]] = relationship()
    attempts: Mapped[list["Attempt"]] = relationship()
    adaptive_events: Mapped[list["AdaptiveEvent"]] = relationship(order_by="AdaptiveEvent.round_no, AdaptiveEvent.event_type")


class TabLeaveInterval(Base):
    """Server-timed leave/return interval for FIXED-paper anti-cheat.

    The client supplies opaque event ids only; ``left_at`` and
    ``returned_at`` are server clock values. At most one interval per session
    may be open (database partial unique index). Short intervals are stored
    but not counted.
    """

    __tablename__ = "tab_leave_interval"
    __table_args__ = (CheckConstraint("away_seconds IS NULL OR away_seconds >= 0"),)

    leave_event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_session.session_id", ondelete="CASCADE"))
    left_at: Mapped[datetime]
    returned_at: Mapped[Optional[datetime]]
    return_event_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), unique=True)
    away_seconds: Mapped[Optional[int]]
    counted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class AdaptiveEvent(Base):
    __tablename__ = "adaptive_event"
    __table_args__ = (CheckConstraint("round_no BETWEEN 1 AND 13"),
                      CheckConstraint("event_type IN ('batch', 'decision')"))
    session_id: Mapped[int] = mapped_column(ForeignKey("assessment_session.session_id"), primary_key=True)
    round_no: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class SessionStartRequest(Base):
    """Immutable learner-scoped bindings for both original and resume requests."""

    __tablename__ = "session_start_request"
    __table_args__ = (ForeignKeyConstraint(
        ["session_id", "learner_id"],
        ["assessment_session.session_id", "assessment_session.learner_id"]),)
    learner_id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Attempt(Base):
    """One row per served question. A row is graded iff submitted_at is set."""

    __tablename__ = "attempt"
    __table_args__ = (
        UniqueConstraint("session_id", "seq_no"),
        CheckConstraint("flag_revision >= 0"),
    )

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
    review_revision: Mapped[int] = mapped_column(default=0)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    flag_revision: Mapped[int] = mapped_column(default=0)
    first_opened_at: Mapped[Optional[datetime]]

    question: Mapped[Question] = relationship()
    session: Mapped[AssessmentSession] = relationship(back_populates="attempts")


class SessionQuestionPlan(Base):
    __tablename__ = "session_question_plan"
    __table_args__ = (UniqueConstraint("session_id", "question_id"), CheckConstraint("seq_no > 0"))
    session_id: Mapped[int] = mapped_column(ForeignKey("assessment_session.session_id"), primary_key=True)
    seq_no: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"))


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
    points_earned: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    points_possible: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
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
    expires_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc) + timedelta(days=60)
    )


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


class PasswordResetToken(Base):
    __tablename__ = "password_reset_token"
    __table_args__ = (CheckConstraint("expires_at > requested_at"),)

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    requested_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime]
    used_at: Mapped[Optional[datetime]]
    revoked_at: Mapped[Optional[datetime]]


class PasswordResetAudit(Base):
    __tablename__ = "password_reset_audit"
    __table_args__ = (CheckConstraint("event IN ('requested','completed')"),)

    audit_id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    event: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


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


class GradeReview(Base):
    __tablename__ = "grade_review"
    __table_args__ = (CheckConstraint("approved_score >= 0"),)
    review_id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempt.attempt_id"), unique=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    automated_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    automated_detail: Mapped[Optional[dict]] = mapped_column(JSONB)
    approved_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    comments: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ResultReleaseEvent(Base):
    __tablename__ = "result_release_event"
    event_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("assessment_session.session_id"))
    previous_status: Mapped[str] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20))
    reviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class RefreshSession(Base):
    __tablename__ = "refresh_session"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(32), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.account_id", ondelete="CASCADE"), index=True)
    credential_version: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime]
    consumed_at: Mapped[Optional[datetime]]
    revoked_at: Mapped[Optional[datetime]]


class SystemSetting(Base):
    __tablename__ = "system_setting"
    setting_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB)
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class EvaluationRecord(Base):
    __tablename__ = "evaluation_record"
    __table_args__ = (UniqueConstraint("learner_id", "scope_key"),)
    evaluation_id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assessment_session.session_id"))
    scope_key: Mapped[str] = mapped_column(String(80))
    input_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    lease_until: Mapped[Optional[datetime]]
    available_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class GradeEditAudit(Base):
    __tablename__ = "grade_edit_audit"
    audit_id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempt.attempt_id"))
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    old_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    new_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    reason: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class SessionFinalResult(Base):
    """Immutable administrator-approved result for one practice session."""

    __tablename__ = "session_final_result"
    __table_args__ = (
        CheckConstraint("source IN ('admin','legacy')"),
        CheckConstraint("approval_revision >= 0"),
    )

    result_id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_session.session_id"), unique=True
    )
    reviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))
    source: Mapped[str] = mapped_column(String(20), default="admin")
    evaluation_input_hash: Mapped[str] = mapped_column(String(64))
    approval_revision: Mapped[int] = mapped_column(default=0)
    ai_evaluation: Mapped[dict] = mapped_column(JSONB)
    final_evaluation: Mapped[dict] = mapped_column(JSONB)
    concept_results: Mapped[list] = mapped_column(JSONB, default=list)
    scores: Mapped[list] = mapped_column(JSONB, default=list)
    overall: Mapped[dict] = mapped_column(JSONB)
    uncovered_concepts: Mapped[list] = mapped_column(JSONB, default=list)
    approved_at: Mapped[datetime] = mapped_column(server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class AssessmentQuestion(Base):
    __tablename__ = "assessment_question"

    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessment.assessment_id", ondelete="CASCADE"), primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"), primary_key=True)


class QuestionRubricProfile(Base):
    __tablename__ = "question_rubric_profile"
    __table_args__ = (
        UniqueConstraint("question_id", "version_no"),
        UniqueConstraint("question_id", "rubric_profile_id"),
        CheckConstraint("version_no > 0"),
        CheckConstraint("status IN ('active','retired')"),
    )

    rubric_profile_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"))
    version_no: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(10))
    profile_hash: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    retired_at: Mapped[Optional[datetime]]


class QuestionRubricCriterion(Base):
    __tablename__ = "question_rubric_criterion"
    __table_args__ = (
        UniqueConstraint("rubric_profile_id", "criterion_code"),
        UniqueConstraint("rubric_profile_id", "sort_order"),
        CheckConstraint("max_points > 0"),
        CheckConstraint("sort_order > 0"),
    )

    criterion_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rubric_profile_id: Mapped[int] = mapped_column(
        ForeignKey("question_rubric_profile.rubric_profile_id")
    )
    criterion_code: Mapped[str] = mapped_column(String(40))
    criterion_name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    scoring_guidance: Mapped[str] = mapped_column(Text)
    max_points: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    sort_order: Mapped[int] = mapped_column(SmallInteger)
    criterion_hash: Mapped[str] = mapped_column(String(64))


class AttemptRubricCriterion(Base):
    __tablename__ = "attempt_rubric_criterion"
    __table_args__ = (
        UniqueConstraint("session_id", "attempt_id", "criterion_snapshot_id"),
        UniqueConstraint("attempt_id", "criterion_id"),
        ForeignKeyConstraint(
            ["session_id", "attempt_id"], ["attempt.session_id", "attempt.attempt_id"]
        ),
        ForeignKeyConstraint(
            ["question_id", "rubric_profile_id"],
            ["question_rubric_profile.question_id", "question_rubric_profile.rubric_profile_id"],
        ),
    )

    criterion_snapshot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int]
    attempt_id: Mapped[int]
    question_id: Mapped[int]
    rubric_profile_id: Mapped[int]
    criterion_id: Mapped[int] = mapped_column(
        ForeignKey("question_rubric_criterion.criterion_id")
    )
    criterion_code: Mapped[str] = mapped_column(String(40))
    criterion_name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    scoring_guidance: Mapped[str] = mapped_column(Text)
    max_points: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    sort_order: Mapped[int] = mapped_column(SmallInteger)
    profile_snapshot_hash: Mapped[str] = mapped_column(String(64))
    criterion_hash: Mapped[str] = mapped_column(String(64))


class SessionResultVersion(Base):
    __tablename__ = "session_result_version"
    __table_args__ = (
        UniqueConstraint("session_id", "version_no"),
        UniqueConstraint("session_id", "result_version_id"),
        CheckConstraint("version_no >= 1"),
        CheckConstraint("total_score >= 0 AND total_score <= max_score"),
        CheckConstraint("source IN ('V1','V2')"),
        CheckConstraint("source = 'V1' OR approved_by IS NOT NULL"),
    )

    result_version_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("assessment_session.session_id"))
    version_no: Mapped[int]
    source: Mapped[str] = mapped_column(String(10))
    supersedes_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("session_result_version.result_version_id")
    )
    total_score: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    max_score: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    result_hash: Mapped[str] = mapped_column(String(64))
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))
    approved_at: Mapped[datetime] = mapped_column(server_default=func.now())
    approved_draft_hash: Mapped[Optional[str]] = mapped_column(String(64))
    approved_review_revision: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    review_request_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "review_request.review_request_id",
            deferrable=True,
            initially="DEFERRED",
        )
    )


class SessionResultVersionScore(Base):
    __tablename__ = "session_result_version_score"
    __table_args__ = (
        UniqueConstraint("session_id", "result_version_id", "attempt_id"),
        ForeignKeyConstraint(
            ["session_id", "result_version_id"],
            ["session_result_version.session_id", "session_result_version.result_version_id"],
        ),
        ForeignKeyConstraint(
            ["session_id", "attempt_id"], ["attempt.session_id", "attempt.attempt_id"]
        ),
        CheckConstraint("score >= 0 AND score <= max_score"),
        CheckConstraint("source IN ('MACHINE','AI2','REVIEW','REGRADE')"),
    )

    version_score_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int]
    result_version_id: Mapped[int]
    attempt_id: Mapped[int]
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    max_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    source: Mapped[str] = mapped_column(String(20))


class SessionResultCriterionScore(Base):
    __tablename__ = "session_result_criterion_score"
    __table_args__ = (
        UniqueConstraint("session_id", "result_version_id", "attempt_id", "criterion_snapshot_id"),
        ForeignKeyConstraint(
            ["session_id", "result_version_id", "attempt_id"],
            [
                "session_result_version_score.session_id",
                "session_result_version_score.result_version_id",
                "session_result_version_score.attempt_id",
            ],
        ),
        ForeignKeyConstraint(
            ["session_id", "attempt_id", "criterion_snapshot_id"],
            [
                "attempt_rubric_criterion.session_id",
                "attempt_rubric_criterion.attempt_id",
                "attempt_rubric_criterion.criterion_snapshot_id",
            ],
        ),
        CheckConstraint("score >= 0 AND score <= max_points"),
    )

    criterion_score_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int]
    result_version_id: Mapped[int]
    attempt_id: Mapped[int]
    criterion_snapshot_id: Mapped[int]
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    max_points: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    comment: Mapped[Optional[str]] = mapped_column(String(2000))


class SessionResultPublication(Base):
    __tablename__ = "session_result_publication"
    __table_args__ = (
        UniqueConstraint("session_id", "result_version_id"),
        ForeignKeyConstraint(
            ["session_id", "result_version_id"],
            ["session_result_version.session_id", "session_result_version.result_version_id"],
        ),
        CheckConstraint(
            "state IN ('APPROVED_PENDING_ANALYSIS','ANALYSIS_FAILED','OFFICIAL')"
        ),
        CheckConstraint("state_revision >= 0"),
    )

    result_version_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int]
    state: Mapped[str] = mapped_column(String(30))
    state_revision: Mapped[int] = mapped_column(default=0)
    published_at: Mapped[Optional[datetime]]
    analysis_failed_at: Mapped[Optional[datetime]]
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))


class AiStageRun(Base):
    __tablename__ = "ai_stage_run"
    __table_args__ = (
        UniqueConstraint("stage_run_id", "session_id"),
        UniqueConstraint("session_id", "scope_key", "stage", "execution_run_no"),
        CheckConstraint("scope_key = 'v1' OR scope_key ~ '^v2:[1-9][0-9]*$'"),
        CheckConstraint("stage IN ('AI1','AI2')"),
        CheckConstraint("run_mode IN ('V1_GRADING','V2_ANALYSIS')"),
        CheckConstraint("status IN ('PENDING','PROCESSING','RETRY_WAIT','COMPLETED','FAILED','CANCELLED')"),
        CheckConstraint("attempt_count BETWEEN 0 AND 3"),
        CheckConstraint("execution_run_no >= 1"),
        CheckConstraint(
            "(scope_key = 'v1' AND run_mode = 'V1_GRADING') OR "
            "(scope_key ~ '^v2:[1-9][0-9]*$' AND run_mode = 'V2_ANALYSIS')"
        ),
        CheckConstraint(
            "(stage = 'AI1' AND predecessor_validation_id IS NULL) OR "
            "(stage = 'AI2' AND predecessor_validation_id IS NOT NULL)"
        ),
    )

    stage_run_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("assessment_session.session_id"))
    scope_key: Mapped[str] = mapped_column(String(40))
    stage: Mapped[str] = mapped_column(String(3))
    run_mode: Mapped[str] = mapped_column(String(20))
    result_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("session_result_version.result_version_id")
    )
    execution_run_no: Mapped[int]
    recovery_of_run_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ai_stage_run.stage_run_id")
    )
    recovery_authorized_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("account.account_id")
    )
    recovery_reason: Mapped[Optional[str]] = mapped_column(String(1000))
    predecessor_validation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ai_stage_validation.validation_id")
    )
    status: Mapped[str] = mapped_column(String(20))
    attempt_count: Mapped[int] = mapped_column(default=0)
    input_hash: Mapped[str] = mapped_column(String(64))
    output_hash: Mapped[Optional[str]] = mapped_column(String(64))
    last_error_code: Mapped[Optional[str]] = mapped_column(String(80))
    available_at: Mapped[datetime] = mapped_column(server_default=func.now())
    lease_until: Mapped[Optional[datetime]]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    started_at: Mapped[Optional[datetime]]
    finished_at: Mapped[Optional[datetime]]


class AiStageValidation(Base):
    __tablename__ = "ai_stage_validation"
    __table_args__ = (
        UniqueConstraint("stage_run_id"),
        ForeignKeyConstraint(
            ["stage_run_id", "session_id"], ["ai_stage_run.stage_run_id", "ai_stage_run.session_id"]
        ),
        CheckConstraint("status IN ('VALID','INVALID')"),
    )

    validation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int]
    stage_run_id: Mapped[int]
    validator_version: Mapped[str] = mapped_column(String(40))
    input_hash: Mapped[str] = mapped_column(String(64))
    output_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(10))
    validated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class AiStageAttempt(Base):
    __tablename__ = "ai_stage_attempt"
    __table_args__ = (
        UniqueConstraint("session_id", "stage_run_id", "attempt_no"),
        ForeignKeyConstraint(
            ["stage_run_id", "session_id"], ["ai_stage_run.stage_run_id", "ai_stage_run.session_id"]
        ),
        CheckConstraint("attempt_no BETWEEN 1 AND 3"),
        CheckConstraint("status IN ('STARTED','SUCCEEDED','FAILED')"),
    )

    stage_attempt_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int]
    stage_run_id: Mapped[int]
    attempt_no: Mapped[int]
    status: Mapped[str] = mapped_column(String(20))
    input_hash: Mapped[str] = mapped_column(String(64))
    output_hash: Mapped[Optional[str]] = mapped_column(String(64))
    error_code: Mapped[Optional[str]] = mapped_column(String(80))
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    finished_at: Mapped[Optional[datetime]]


class AiPromptRecord(Base):
    __tablename__ = "ai_prompt_record"
    __table_args__ = (
        ForeignKeyConstraint(
            ["stage_run_id", "session_id"], ["ai_stage_run.stage_run_id", "ai_stage_run.session_id"]
        ),
        CheckConstraint("stage IN ('AI1','AI2')"),
    )

    prompt_record_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int]
    stage_run_id: Mapped[int]
    stage: Mapped[str] = mapped_column(String(3))
    prompt_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime]
    purged_at: Mapped[Optional[datetime]]


class AiPromptContent(Base):
    __tablename__ = "ai_prompt_content"

    prompt_record_id: Mapped[int] = mapped_column(
        ForeignKey("ai_prompt_record.prompt_record_id"), primary_key=True
    )
    prompt_text: Mapped[Optional[str]] = mapped_column(Text)
    model_identifier: Mapped[Optional[str]] = mapped_column(String(80))


class RetentionPurgeAudit(Base):
    __tablename__ = "retention_purge_audit"
    __table_args__ = (
        CheckConstraint("object_type IN ('PROMPT_CONTENT','LLM_CACHE')"),
        CheckConstraint("purge_reason IN ('AGE_60_DAYS','MANUAL_ADMIN','MIGRATION_BACKFILL')"),
    )

    purge_audit_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    object_type: Mapped[str] = mapped_column(String(20))
    object_id: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))
    purged_at: Mapped[datetime] = mapped_column(server_default=func.now())
    purge_reason: Mapped[str] = mapped_column(String(40))
    actor: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class PromptAccessAudit(Base):
    __tablename__ = "prompt_access_audit"
    __table_args__ = (
        CheckConstraint("result IN ('GRANTED','DENIED_EXPIRED','DENIED_PURGED')"),
    )

    access_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    prompt_record_id: Mapped[int] = mapped_column(
        ForeignKey("ai_prompt_record.prompt_record_id")
    )
    actor_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    result: Mapped[str] = mapped_column(String(20))
    accessed_at: Mapped[datetime] = mapped_column(server_default=func.now())
    request_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))


class SessionResultAnalysis(Base):
    __tablename__ = "session_result_analysis"
    __table_args__ = (
        UniqueConstraint("session_id", "result_version_id"),
        ForeignKeyConstraint(
            ["session_id", "result_version_id"],
            ["session_result_version.session_id", "session_result_version.result_version_id"],
        ),
        ForeignKeyConstraint(
            ["ai1_run_id", "session_id"], ["ai_stage_run.stage_run_id", "ai_stage_run.session_id"]
        ),
        ForeignKeyConstraint(
            ["ai2_run_id", "session_id"], ["ai_stage_run.stage_run_id", "ai_stage_run.session_id"]
        ),
        CheckConstraint("analysis_schema_version > 0"),
    )

    analysis_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int]
    result_version_id: Mapped[int]
    ai1_run_id: Mapped[int]
    ai2_run_id: Mapped[int]
    analysis_schema_version: Mapped[int]
    analysis_hash: Mapped[str] = mapped_column(String(64))
    analysis: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ReviewRequest(Base):
    """One review case per session; the only v2 entry point."""

    __tablename__ = "review_request"
    __table_args__ = (
        UniqueConstraint("session_id"),
        UniqueConstraint("request_key"),
        ForeignKeyConstraint(
            ["session_id", "base_result_version_id"],
            ["session_result_version.session_id", "session_result_version.result_version_id"],
        ),
        ForeignKeyConstraint(
            ["session_id", "regraded_result_version_id"],
            ["session_result_version.session_id", "session_result_version.result_version_id"],
        ),
        CheckConstraint("origin IN ('LEARNER','ADMIN_REPORT','ADMIN')"),
        CheckConstraint(
            "status IN ('REQUESTED','IN_REVIEW','REGRADED','REJECTED','EXPIRED')"
        ),
        CheckConstraint("length(btrim(reason)) >= 10"),
        CheckConstraint("origin <> 'LEARNER' OR window_expires_at IS NOT NULL"),
        CheckConstraint(
            "claimed_by IS NULL OR (claimed_at IS NOT NULL AND claim_expires_at IS NOT NULL)"
        ),
        CheckConstraint("status <> 'REGRADED' OR regraded_result_version_id IS NOT NULL"),
        CheckConstraint(
            "status NOT IN ('REGRADED','REJECTED') OR resolved_at IS NOT NULL"
        ),
        Index("review_request_queue_idx", "status", "created_at"),
    )

    review_request_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_session.session_id")
    )
    learner_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    requested_by: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    origin: Mapped[str] = mapped_column(String(12))
    request_key: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    reason: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(20), default="REQUESTED")
    base_result_version_id: Mapped[int]
    requested_at: Mapped[datetime] = mapped_column(server_default=func.now())
    window_expires_at: Mapped[Optional[datetime]]
    claimed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))
    claimed_at: Mapped[Optional[datetime]]
    claim_expires_at: Mapped[Optional[datetime]]
    resolved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))
    resolved_at: Mapped[Optional[datetime]]
    resolution_note: Mapped[Optional[str]] = mapped_column(String(2000))
    regraded_result_version_id: Mapped[Optional[int]]
    revision: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class QuestionReport(Base):
    """Wrong question/answer evidence; acceptance drives a regrade."""

    __tablename__ = "question_report"
    __table_args__ = (
        UniqueConstraint("session_id", "attempt_id", "category"),
        ForeignKeyConstraint(
            ["session_id", "attempt_id"],
            ["attempt.session_id", "attempt.attempt_id"],
        ),
        CheckConstraint(
            "category IN ('WRONG_ANSWER','WRONG_QUESTION','AMBIGUOUS','TECHNICAL')"
        ),
        CheckConstraint("status IN ('OPEN','ACCEPTED','REJECTED')"),
        CheckConstraint("length(btrim(details)) >= 10"),
        CheckConstraint("status = 'OPEN' OR resolved_at IS NOT NULL"),
        Index("question_report_open_idx", "status", "created_at"),
        Index("question_report_review_idx", "review_request_id", "status"),
    )

    question_report_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    review_request_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("review_request.review_request_id")
    )
    session_id: Mapped[int]
    attempt_id: Mapped[int]
    question_id: Mapped[int] = mapped_column(ForeignKey("question.question_id"))
    reported_by: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    category: Mapped[str] = mapped_column(String(20))
    details: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(10), default="OPEN")
    resolution_note: Mapped[Optional[str]] = mapped_column(String(2000))
    resolved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("account.account_id"))
    resolved_at: Mapped[Optional[datetime]]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ReviewDeviation(Base):
    """Append-only >30% score-change evidence: second admin or long reason."""

    __tablename__ = "review_deviation"
    __table_args__ = (
        ForeignKeyConstraint(
            ["session_id", "attempt_id"],
            ["attempt.session_id", "attempt.attempt_id"],
        ),
        ForeignKeyConstraint(
            ["session_id", "attempt_id", "criterion_snapshot_id"],
            [
                "attempt_rubric_criterion.session_id",
                "attempt_rubric_criterion.attempt_id",
                "attempt_rubric_criterion.criterion_snapshot_id",
            ],
        ),
        CheckConstraint("max_points > 0"),
        CheckConstraint("deviation_ratio > 0.30"),
        CheckConstraint(
            "deviation_ratio = round(abs(reviewed_score - ai_score) / max_points, 4)"
        ),
        CheckConstraint(
            "second_reviewer_id IS NULL OR second_reviewer_id <> first_reviewer_id"
        ),
        CheckConstraint(
            "(confirmation = 'SECOND_ADMIN') = (second_reviewer_id IS NOT NULL)"
        ),
        CheckConstraint(
            "confirmation IN ('SECOND_ADMIN','SINGLE_ADMIN_LONG_REASON')"
        ),
        CheckConstraint("length(btrim(reason)) >= 10"),
        CheckConstraint(
            "confirmation <> 'SINGLE_ADMIN_LONG_REASON' OR length(btrim(reason)) >= 120"
        ),
        Index(
            "review_deviation_attempt_uk",
            "review_request_id",
            "attempt_id",
            unique=True,
            postgresql_where=text("criterion_snapshot_id IS NULL"),
        ),
        Index(
            "review_deviation_criterion_uk",
            "review_request_id",
            "attempt_id",
            "criterion_snapshot_id",
            unique=True,
            postgresql_where=text("criterion_snapshot_id IS NOT NULL"),
        ),
    )

    deviation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    review_request_id: Mapped[int] = mapped_column(
        ForeignKey("review_request.review_request_id")
    )
    session_id: Mapped[int]
    attempt_id: Mapped[int]
    criterion_snapshot_id: Mapped[Optional[int]]
    ai_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    reviewed_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    max_points: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    deviation_ratio: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    reason: Mapped[str] = mapped_column(String(4000))
    first_reviewer_id: Mapped[int] = mapped_column(ForeignKey("account.account_id"))
    second_reviewer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("account.account_id")
    )
    confirmation: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
