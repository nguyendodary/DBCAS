"""Identity & Access use cases: UC01 register, UC02 login, UC04 provision.

Owns the account workflow rules (email uniqueness, role assignment, account
status) — routers stay thin and repositories only do persistence.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import Settings
from ..errors import AppError
from ..models import Account
from ..repositories import AccountRepository, CurriculumRepository
from ..schemas import (
    AccountSummary,
    LoginRequest,
    ProvisionAccountRequest,
    RegisterRequest,
)
from ..security import create_access_token, hash_password, verify_password


def to_summary(account: Account) -> AccountSummary:
    return AccountSummary(
        account_id=account.account_id,
        email=account.email,
        full_name=account.profile.full_name if account.profile else None,
        roles=sorted(r.role_name for r in account.roles),
        status=account.status,
    )


def register_learner(db: Session, payload: RegisterRequest) -> AccountSummary:
    """UC01 — self-registration always produces an active Learner account."""
    repo = AccountRepository(db)
    if repo.find_by_email(payload.email) is not None:
        raise AppError(409, "email_taken", "Email is already registered")
    try:
        account = repo.create_learner(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.name.strip(),
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "email_taken", "Email is already registered")
    db.refresh(account)
    return to_summary(account)


def login(db: Session, payload: LoginRequest, settings: Settings) -> tuple[str, int, AccountSummary]:
    """UC02 — credentials + active status required; issues a JWT."""
    account = AccountRepository(db).find_by_email(payload.email)
    if account is None or not verify_password(payload.password, account.password_hash):
        raise AppError(401, "invalid_credentials", "Invalid email or password")
    if account.status != "active":
        raise AppError(403, "account_disabled", "Account is not active")
    roles = sorted(r.role_name for r in account.roles)
    token, expires_in = create_access_token(account.account_id, roles, settings)
    return token, expires_in, to_summary(account)


def provision_account(
    db: Session, payload: ProvisionAccountRequest
) -> AccountSummary:
    """UC04 — admins create accounts; they always start disabled.

    Self-registration (register_learner) can never grant non-Learner roles;
    this endpoint is the only way to create an Administrator.
    """
    if payload.role != "Administrator":
        raise AppError(422, "invalid_role", "Only Administrator provisioning is supported")
    repo = AccountRepository(db)
    if repo.find_by_email(payload.email) is not None:
        raise AppError(409, "email_taken", "Email is already registered")
    try:
        account = repo.create_provisioned(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.name.strip(),
            role_name=payload.role,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "email_taken", "Email is already registered")
    db.refresh(account)
    return to_summary(account)


def list_accounts(db: Session) -> list[AccountSummary]:
    """UC04 — the admin roster (all roles, all statuses)."""
    return [to_summary(a) for a in CurriculumRepository(db).list_accounts()]


def set_account_status(
    db: Session, account_id: int, status: str, actor: Account
) -> AccountSummary:
    """UC04 — activate a verified account or disable one.

    An admin cannot disable their own account (that would lock them out
    mid-session); another admin must do it.
    """
    account = CurriculumRepository(db).get_account(account_id)
    if account is None:
        raise AppError(404, "account_not_found", "Account not found")
    if status == "disabled" and account.account_id == actor.account_id:
        raise AppError(
            409, "cannot_disable_self", "You cannot disable your own account"
        )
    account.status = status
    db.commit()
    db.refresh(account)
    return to_summary(account)
