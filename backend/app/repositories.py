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
    Question,
    Role,
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
