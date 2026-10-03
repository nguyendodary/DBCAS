"""Repository layer: all persistence access for the current endpoints.

Services never write SQLAlchemy queries themselves; they go through these
repositories so the data-access code stays in one place.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .models import (
    Account,
    AssessmentSession,
    Attempt,
    Concept,
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
