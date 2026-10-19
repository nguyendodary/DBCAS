"""Identity & Access use cases: UC01 register, UC02 login, UC04 provision.

Owns the account workflow rules (email uniqueness, role assignment, account
status) — routers stay thin and repositories only do persistence.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import Settings
from ..errors import AppError
from ..models import Account
from ..repositories import AccountRepository, CurriculumRepository, SecurityRepository
from ..schemas import (
    AccountRoleChangeResult,
    AccountRoleUpdate,
    AccountRoleAuditItem,
    AccountSummary,
    LoginRequest,
    ProvisionAccountRequest,
    RegisterRequest,
)
from ..security import create_access_token, hash_password, verify_password

# Same bcrypt work factor as real passwords. Never generate this per request.
_DUMMY_HASH = hash_password("unusable-dummy-authentication-password")


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
    from ..repositories import SecurityRepository
    SecurityRepository(db).lock("email:" + payload.email.strip().lower())
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
    valid = verify_password(payload.password, account.password_hash if account else _DUMMY_HASH)
    if account is None or not valid:
        raise AppError(401, "invalid_credentials", "Invalid email or password")
    if account.status != "active":
        raise AppError(403, "account_disabled", "Account is not active")
    roles = sorted(r.role_name for r in account.roles)
    token, expires_in = create_access_token(account.account_id, roles, settings)
    return token, expires_in, to_summary(account)


def provision_account(
    db: Session, payload: ProvisionAccountRequest, actor: Account
) -> AccountSummary:
    """UC04 — authorized role managers provision disabled Administrator accounts.

    Self-registration (register_learner) can never grant non-Learner roles;
    this is a privileged account operation and shares the role-management guard.
    """
    if payload.role != "Administrator":
        raise AppError(422, "invalid_role", "Only Administrator provisioning is supported")
    SecurityRepository(db).lock("account-security:roles-and-status")
    actor = _locked_role_manager(db, actor.account_id)
    repo = AccountRepository(db)
    SecurityRepository(db).lock("email:" + payload.email.strip().lower())
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
    SecurityRepository(db).lock("account-security:roles-and-status")
    repo = AccountRepository(db)
    actor = repo.get_for_update(actor.account_id)
    if actor is None or actor.status != "active" or not any(r.role_name == "Administrator" for r in actor.roles):
        raise AppError(403, "forbidden", "Insufficient role for this resource")
    account = repo.get_for_update(account_id)
    if account is None:
        raise AppError(404, "account_not_found", "Account not found")
    if status == "disabled" and account.account_id == actor.account_id:
        raise AppError(
            409, "cannot_disable_self", "You cannot disable your own account"
        )
    target_is_admin = _canonical_role(account)
    if target_is_admin == "Administrator":
        if not actor.can_manage_roles:
            raise AppError(403, "role_management_forbidden", "You are not authorized to manage administrator accounts")
        if status == "disabled" and account.status == "active":
            if repo.active_administrator_count() <= 1:
                raise AppError(409, "last_administrator", "The last active Administrator cannot be disabled")
            if account.can_manage_roles and repo.active_role_manager_count() <= 1:
                raise AppError(409, "last_role_manager", "The last active role manager cannot be disabled")
    account.status = status
    db.commit()
    db.refresh(account)
    return to_summary(account)


def role_management_capability(actor: Account) -> dict:
    return {"account_id": actor.account_id, "can_manage_roles": bool(actor.can_manage_roles)}


def set_account_role(
    db: Session, account_id: int, payload: AccountRoleUpdate, actor: Account
) -> AccountRoleChangeResult:
    """Change one account's application role under a serialized transaction."""
    security = SecurityRepository(db)
    security.lock("account-security:roles-and-status")
    actor = _locked_role_manager(db, actor.account_id)
    repo = AccountRepository(db)
    target = repo.get_for_update(account_id)
    if target is None:
        raise AppError(404, "account_not_found", "Account not found")

    current_role = _canonical_role(target)
    if current_role is None:
        raise AppError(409, "account_role_missing", "This account does not have a supported application role")
    if current_role != payload.expected_role:
        raise AppError(409, "role_changed_concurrently", "This account's role changed. Refresh the account list and try again.")
    if payload.role == current_role:
        return AccountRoleChangeResult(account=to_summary(target), changed=False)
    if account_id == actor.account_id and payload.role == "Learner":
        raise AppError(409, "cannot_demote_self", "You cannot revoke Administrator access from your own account")
    if payload.role == "Administrator" and target.status != "active":
        raise AppError(409, "inactive_account_role_change", "Activate and verify this account before granting Administrator access")

    if current_role == "Administrator" and target.status == "active":
        if repo.active_administrator_count() <= 1:
            raise AppError(409, "last_administrator", "The last active Administrator cannot be demoted")
        if target.can_manage_roles and repo.active_role_manager_count() <= 1:
            raise AppError(409, "last_role_manager", "The last active role manager cannot be demoted")

    role = repo.get_role(payload.role)
    if role is None:
        raise AppError(503, "database_schema_unavailable", "Required account roles are unavailable")
    target.roles = [r for r in target.roles if r.role_name not in {"Learner", "Administrator"}]
    target.roles.append(role)
    # Role assignment never grants or carries the separate management capability.
    target.can_manage_roles = False
    repo.add_role_audit(
        action_type="ROLE_GRANTED" if payload.role == "Administrator" else "ROLE_REVOKED",
        actor_account_id=actor.account_id,
        target_account_id=target.account_id,
        previous_role=current_role,
        new_role=payload.role,
    )
    db.commit()
    db.refresh(target)
    return AccountRoleChangeResult(account=to_summary(target), changed=True)


def list_role_audit(db: Session, *, limit: int = 100, offset: int = 0) -> list[AccountRoleAuditItem]:
    return [AccountRoleAuditItem.model_validate(event) for event in AccountRepository(db).role_audit(limit, offset)]


def _canonical_role(account: Account) -> str | None:
    roles = {role.role_name for role in account.roles}
    if "Administrator" in roles:
        return "Administrator"
    if "Learner" in roles:
        return "Learner"
    return None


def _locked_role_manager(db: Session, account_id: int) -> Account:
    actor = AccountRepository(db).get_for_update(account_id)
    if actor is None or actor.status != "active" or not any(r.role_name == "Administrator" for r in actor.roles):
        raise AppError(403, "forbidden", "Insufficient role for this resource")
    if not actor.can_manage_roles:
        raise AppError(403, "role_management_forbidden", "You are not authorized to manage account roles")
    return actor
