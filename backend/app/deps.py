"""Shared FastAPI dependencies: auth guard and role-based access control."""

from typing import Callable

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .db import get_db
from .errors import AppError
from .models import Account
from .repositories import AccountRepository
from .security import decode_access_token

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
    account = AccountRepository(db).get_with_roles(account_id)
    if account is None or account.status != STATUS_ACTIVE:
        raise AppError(401, "invalid_token", "Account is not active or does not exist")
    return account


def require_roles(*roles: str) -> Callable[[Account], Account]:
    """Dependency factory: current account must hold at least one role."""

    def guard(account: Account = Depends(get_current_account)) -> Account:
        account_roles = {r.role_name for r in account.roles}
        if not account_roles.intersection(roles):
            raise AppError(403, "forbidden", "Insufficient role for this resource")
        return account

    return guard


CurrentAccount = Depends(get_current_account)
LearnerOnly = Depends(require_roles(ROLE_LEARNER))
AdminOnly = Depends(require_roles(ROLE_ADMIN))


def get_sandbox_runner(
    settings: Settings = Depends(get_settings),
) -> "SandboxRunner":
    """Build a Sandbox Runner bound to the configured sandbox container."""
    from .services.sandbox_runner import SandboxRunner

    return SandboxRunner(settings)


def get_llm_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> "LLMService":
    """LLM service with the DB-backed response cache. Builds fine without a
    key — AI features report ``llm_not_configured`` instead of crashing."""
    from .services.llm import LLMService, build_llm_service

    return build_llm_service(settings, db)
