"""Shared FastAPI dependencies: auth guard and role-based access control."""

from typing import TYPE_CHECKING, Callable

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .db import get_db
from .errors import AppError
from .models import Account
from .repositories import AccountRepository
from .security import credential_epoch, decode_access_token

if TYPE_CHECKING:
    from .services.llm import LLMService
    from .services.sandbox_runner import SandboxRunner

ROLE_LEARNER = "Learner"
ROLE_ADMIN = "Administrator"

# Account.status values (UC02/UC04)
STATUS_ACTIVE = "active"
STATUS_DISABLED = "disabled"


def get_current_account(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Account:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError(401, "missing_token", "Authorization Bearer token is required")
    payload = decode_access_token(authorization.removeprefix("Bearer ").strip(), settings)
    try:
        account_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise AppError(401, "invalid_token", "Token subject is not an account id")
    pwd_at = payload.get("pwd_at", 0)
    if type(pwd_at) is not int:
        raise AppError(401, "invalid_token", "Token has an invalid credential version")
    account = AccountRepository(db).get_with_roles(account_id)
    if account is None or account.status != STATUS_ACTIVE:
        raise AppError(401, "invalid_token", "Account is not active or does not exist")
    if pwd_at != credential_epoch(account.password_changed_at):
        # Issued before the current password; a reset already invalidated it.
        raise AppError(401, "invalid_token", "Credentials have changed — sign in again")
    if "sid" in payload:
        from sqlalchemy import select, func
        from .models import RefreshSession
        family = payload["sid"]
        if not isinstance(family, str) or not db.scalar(select(RefreshSession.token_hash).where(
            RefreshSession.family_id == family, RefreshSession.account_id == account_id,
            RefreshSession.revoked_at.is_(None), RefreshSession.consumed_at.is_(None),
            RefreshSession.expires_at > func.now(),
        ).limit(1)):
            raise AppError(401, "invalid_token", "Access session has been revoked")
    return account


def require_roles(*roles: str) -> Callable[[Account], Account]:
    """Dependency factory: current account must hold at least one role."""

    def guard(account: Account = Depends(get_current_account)) -> Account:
        account_roles = {r.role_name for r in account.roles}
        if not account_roles.intersection(roles):
            raise AppError(403, "forbidden", "Insufficient role for this resource")
        return account

    guard.required_roles = roles
    return guard


CurrentAccount = Depends(get_current_account)
LearnerOnly = Depends(require_roles(ROLE_LEARNER))
AdminOnly = Depends(require_roles(ROLE_ADMIN))


def require_role_manager(account: Account = AdminOnly) -> Account:
    """Role assignment is a separate capability, never implied by admin role."""
    if not account.can_manage_roles:
        raise AppError(403, "role_management_forbidden", "You are not authorized to manage account roles")
    return account


RoleManagerOnly = Depends(require_role_manager)


def get_sandbox_runner(
    settings: Settings = Depends(get_settings),
) -> "SandboxRunner":
    """Build a Sandbox Runner bound to the configured sandbox container."""
    from .services.sandbox_runner import build_sandbox_runner

    return build_sandbox_runner(settings)


def get_llm_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> "LLMService":
    """LLM service with the DB-backed response cache. Builds fine without a
    key — AI features report ``llm_not_configured`` instead of crashing."""
    from .services.llm import build_llm_service

    return build_llm_service(settings, db)


def get_translation_llm(settings: Settings = Depends(get_settings)):
    """Drafts have no database cache; at most one bounded provider attempt."""
    from .services.llm import LLMService
    return LLMService(settings.model_copy(update={
        "llm_max_retries": 0, "llm_timeout_seconds": max(1, min(30, settings.llm_timeout_seconds)),
    }))
