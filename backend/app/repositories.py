"""Repository layer: all persistence access for the current endpoints.

Services never write SQLAlchemy queries themselves; they go through these
repositories so the data-access code stays in one place.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from .models import (
    Account,
    AssessmentConcept,
    AssessmentSession,
    Attempt,
    CompetencyGap,
    Concept,
    ConceptCompetency,
    ConceptDependency,
    LlmCache,
    Question,
    QuestionConcept,
    Role,
    Rubric,
    SqlTestDataset,
    UserProfile,
)


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_email(self, email: str) -> Optional[Account]:
        return self.db.scalar(
            select(Account)
            .options(selectinload(Account.roles), selectinload(Account.profile))
            .where(Account.email == email)
        )

    def get_with_roles(self, account_id: int) -> Optional[Account]:
        return self.db.scalar(
            select(Account)
            .options(selectinload(Account.roles), selectinload(Account.profile))
            .where(Account.account_id == account_id)
        )

    def get_role(self, role_name: str) -> Optional[Role]:
        return self.db.scalar(select(Role).where(Role.role_name == role_name))

    def create_learner(self, email: str, password_hash: str, full_name: str) -> Account:
        """UC01: account + profile + Learner role, always status=active."""
        account = Account(email=email, password_hash=password_hash, status="active")
        account.profile = UserProfile(full_name=full_name)
        role = self.get_role("Learner")
        if role is None:
            raise RuntimeError("Role 'Learner' is not seeded — run db/seed.sql")
        account.roles.append(role)
        self.db.add(account)
        return account

    def create_provisioned(
        self, email: str, password_hash: str, full_name: str, role_name: str
    ) -> Account:
        """UC04: admin-provisioned accounts always start disabled."""
        account = Account(email=email, password_hash=password_hash, status="disabled")
        account.profile = UserProfile(full_name=full_name)
        role = self.get_role(role_name)
        if role is None:
            raise RuntimeError(f"Role '{role_name}' is not seeded — run db/seed.sql")
        account.roles.append(role)
        self.db.add(account)
        return account


class AssessmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_session(self, session_id: int) -> Optional[AssessmentSession]:
        return self.db.get(AssessmentSession, session_id)

    def sessions_for_learner(self, learner_id: int) -> list[AssessmentSession]:
        """The learner's own sessions, newest first (UC18 history list)."""
        return list(
            self.db.scalars(
                select(AssessmentSession)
                .options(selectinload(AssessmentSession.assessment))
                .where(AssessmentSession.learner_id == learner_id)
                .order_by(
                    AssessmentSession.started_at.desc(),
                    AssessmentSession.session_id.desc(),
                )
            )
        )

    def attempt_counts(self, session_ids: list[int]) -> dict[int, tuple[int, int]]:
        """session_id -> (served, submitted) attempt counts in one query."""
        if not session_ids:
            return {}
        rows = self.db.execute(
            select(
                Attempt.session_id,
                func.count(Attempt.attempt_id),
                func.count(Attempt.submitted_at),
            )
            .where(Attempt.session_id.in_(session_ids))
            .group_by(Attempt.session_id)
        ).all()
        return {sid: (served, answered) for sid, served, answered in rows}

    def get_question_with_options(self, question_id: int) -> Optional[Question]:
        return self.db.scalar(
            select(Question)
            .options(selectinload(Question.options))
            .where(Question.question_id == question_id)
        )

    def get_attempt(self, session_id: int, question_id: int) -> Optional[Attempt]:
        return self.db.scalar(
            select(Attempt)
            .options(selectinload(Attempt.question).selectinload(Question.options))
            .where(
                Attempt.session_id == session_id,
                Attempt.question_id == question_id,
            )
        )

    def get_datasets_for_question(self, question_id: int) -> list[SqlTestDataset]:
        """All test datasets of a SQL question — regular cases first."""
        return list(
            self.db.scalars(
                select(SqlTestDataset)
                .where(SqlTestDataset.question_id == question_id)
                .order_by(SqlTestDataset.is_edge_case, SqlTestDataset.dataset_id)
            )
        )

    def get_required_concepts(self, question_id: int) -> list[str]:
        """Names of concepts the question mandates (is_required tags)."""
        return list(
            self.db.scalars(
                select(Concept.concept_name)
                .join(
                    QuestionConcept,
                    QuestionConcept.concept_id == Concept.concept_id,
                )
                .where(
                    QuestionConcept.question_id == question_id,
                    QuestionConcept.is_required.is_(True),
                )
                .order_by(Concept.concept_name)
            )
        )

    def get_rubrics_for_question(self, question_id: int) -> list[Rubric]:
        """All rubric rows of an essay question, ordered by level floor."""
        return list(
            self.db.scalars(
                select(Rubric)
                .where(Rubric.question_id == question_id)
                .order_by(Rubric.min_score)
            )
        )


class ConceptGraphRepository:
    """concept / concept_dependency access — the prerequisite skill graph.

    Every read returns rows in a deterministic order so the graph services
    built on top never depend on database ordering luck.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_concept(self, concept_id: int) -> Optional[Concept]:
        return self.db.get(Concept, concept_id)

    def get_concepts(self, concept_ids: set[int]) -> list[Concept]:
        if not concept_ids:
            return []
        return list(
            self.db.scalars(
                select(Concept)
                .where(Concept.concept_id.in_(concept_ids))
                .order_by(Concept.concept_id)
            )
        )

    def list_concepts(self) -> list[Concept]:
        return list(self.db.scalars(select(Concept).order_by(Concept.concept_id)))

    def all_edges(self) -> list[ConceptDependency]:
        return list(
            self.db.scalars(
                select(ConceptDependency).order_by(
                    ConceptDependency.concept_id,
                    ConceptDependency.prerequisite_concept_id,
                )
            )
        )

    def prerequisites_of(self, concept_id: int) -> list[ConceptDependency]:
        return list(
            self.db.scalars(
                select(ConceptDependency)
                .where(ConceptDependency.concept_id == concept_id)
                .order_by(ConceptDependency.prerequisite_concept_id)
            )
        )

    def dependents_of(self, concept_id: int) -> list[ConceptDependency]:
        return list(
            self.db.scalars(
                select(ConceptDependency)
                .where(ConceptDependency.prerequisite_concept_id == concept_id)
                .order_by(ConceptDependency.concept_id)
            )
        )

    def replace_prerequisites(
        self, concept_id: int, prerequisite_ids: list[int]
    ) -> None:
        """Replace one concept's direct prerequisite set atomically."""
        for edge in self.prerequisites_of(concept_id):
            self.db.delete(edge)
        for pid in prerequisite_ids:
            self.db.add(
                ConceptDependency(
                    concept_id=concept_id, prerequisite_concept_id=pid
                )
            )
        self.db.flush()


class CompetencyRepository:
    """concept_competency / competency_gap persistence.

    Rows are keyed (session_id, concept_id) — recompute upserts in place so
    recalculation never duplicates a competency or gap record.
    """

    def __init__(self, db: Session):
        self.db = db

    def session_evidence(self, session_id: int) -> list[Attempt]:
        """The session's graded attempts with their questions' concept tags.

        A served attempt becomes evidence only once submitted — the Sprint 3
        graders persist a deterministic ``attempt.score`` this pipeline reads.
        """
        return list(
            self.db.scalars(
                select(Attempt)
                .options(
                    selectinload(Attempt.question).selectinload(
                        Question.concept_tags
                    )
                )
                .where(
                    Attempt.session_id == session_id,
                    Attempt.submitted_at.is_not(None),
                    Attempt.score.is_not(None),
                )
                .order_by(Attempt.seq_no)
            )
        )

    def assessment_targets(self, assessment_id: int) -> dict[int, Decimal]:
        """concept_id -> administrator-set passing benchmark (target_pct)."""
        rows = self.db.scalars(
            select(AssessmentConcept).where(
                AssessmentConcept.assessment_id == assessment_id
            )
        )
        return {r.concept_id: r.target_pct for r in rows}

    def competencies_for_session(self, session_id: int) -> list[ConceptCompetency]:
        return list(
            self.db.scalars(
                select(ConceptCompetency)
                .options(selectinload(ConceptCompetency.concept))
                .where(ConceptCompetency.session_id == session_id)
                .order_by(ConceptCompetency.concept_id)
            )
        )

    def upsert_competency(
        self,
        session_id: int,
        concept_id: int,
        *,
        points_earned: Decimal,
        points_possible: Decimal,
        competency_pct: Decimal,
        below_target: bool,
    ) -> ConceptCompetency:
        row = self.db.scalar(
            select(ConceptCompetency).where(
                ConceptCompetency.session_id == session_id,
                ConceptCompetency.concept_id == concept_id,
            )
        )
        if row is None:
            row = ConceptCompetency(session_id=session_id, concept_id=concept_id)
            self.db.add(row)
        row.points_earned = points_earned
        row.points_possible = points_possible
        row.competency_pct = competency_pct
        row.below_target = below_target
        row.computed_at = datetime.now(timezone.utc)
        self.db.flush()
        return row

    def delete_stale_competencies(
        self, session_id: int, keep_concept_ids: set[int]
    ) -> None:
        """Drop competency rows for concepts no longer backed by evidence."""
        for row in self.competencies_for_session(session_id):
            if row.concept_id not in keep_concept_ids:
                self.db.delete(row)
        self.db.flush()

    def gaps_for_session(self, session_id: int) -> list[CompetencyGap]:
        return list(
            self.db.scalars(
                select(CompetencyGap)
                .options(selectinload(CompetencyGap.concept))
                .where(CompetencyGap.session_id == session_id)
                .order_by(CompetencyGap.concept_id)
            )
        )

    def upsert_gap(self, session_id: int, concept_id: int) -> CompetencyGap:
        row = self.db.scalar(
            select(CompetencyGap).where(
                CompetencyGap.session_id == session_id,
                CompetencyGap.concept_id == concept_id,
            )
        )
        if row is None:
            row = CompetencyGap(session_id=session_id, concept_id=concept_id)
            self.db.add(row)
            self.db.flush()
        return row

    def delete_stale_gaps(self, session_id: int, keep_concept_ids: set[int]) -> None:
        """A concept that recovered above its benchmark is no longer a gap."""
        for row in self.gaps_for_session(session_id):
            if row.concept_id not in keep_concept_ids:
                self.db.delete(row)
        self.db.flush()


class LlmCacheRepository:
    """llm_cache — request-hash-keyed response store (NFR-09 caching)."""

    def __init__(self, db: Session):
        self.db = db

    def find(self, request_hash: str) -> Optional[dict]:
        row = self.db.scalar(
            select(LlmCache).where(LlmCache.request_hash == request_hash)
        )
        return row.response if row else None

    def store(self, request_hash: str, task_type: str, model: str, response: dict) -> None:
        # INSERT-first semantics: the unique index on request_hash makes
        # concurrent duplicate stores harmless.
        self.db.add(
            LlmCache(
                request_hash=request_hash,
                task_type=task_type,
                model=model,
                response=response,
            )
        )
        self.db.flush()
