"""Self-service password recovery: request → emailed single-use token → confirm.

Security invariants:

- Only a SHA-256 digest of the token is persisted; the plaintext exists
  solely inside the email message.
- The request endpoint answers identically for unknown, disabled and known
  addresses, and the email is sent from a background task so SMTP latency
  does not reveal address existence through response timing.
- One live token per account: issuing revokes older unredeemed tokens, and
  a successful redemption burns its token and revokes the rest.
- The token row is locked FOR UPDATE before redemption, so two concurrent
  redemptions of the same link cannot both succeed.
- Resetting sets ``password_changed_at``; access tokens carry a matching
  ``pwd_at`` claim, which invalidates every session issued before the
  change. Password hashes use the existing bcrypt path.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..config import Settings
from ..errors import AppError
from ..repositories import AccountRepository, PasswordResetRepository, SecurityRepository
from ..schemas import PasswordResetConfirmRequest
from ..security import hash_password

_TOKEN_BYTES = 32


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def request_reset(db: Session, email: str, settings: Settings) -> tuple[str, str] | None:
    """Issue a token for an active account; None for anything else.

    Returns (plaintext_token, account_email); the caller must deliver the
    message in a background task and must never log or return the token.
    """
    account = AccountRepository(db).find_by_email(email)
    if account is None or account.status != "active":
        return None
    SecurityRepository(db).lock("password-reset:" + str(account.account_id))
    repo = PasswordResetRepository(db)
    repo.prune()
    token = secrets.token_urlsafe(_TOKEN_BYTES)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.password_reset_token_ttl_minutes
    )
    repo.store_token(hash_reset_token(token), account.account_id, expires_at)
    repo.audit(account.account_id, "requested")
    db.commit()
    return token, account.email


def confirm_reset(db: Session, payload: PasswordResetConfirmRequest) -> None:
    repo = PasswordResetRepository(db)
    row = repo.lock_token(hash_reset_token(payload.token))
    now = datetime.now(timezone.utc)
    if (
        row is None
        or row.used_at is not None
        or row.revoked_at is not None
        or row.expires_at <= now
    ):
        raise AppError(
            400, "invalid_reset_token", "This reset link is invalid or has expired"
        )
    account = AccountRepository(db).get_for_update(row.account_id)
    if account is None or account.status != "active":
        raise AppError(
            400, "invalid_reset_token", "This reset link is invalid or has expired"
        )
    account.password_hash = hash_password(payload.password)
    account.password_set = True
    account.password_changed_at = now
    row.used_at = now
    repo.revoke_others(account.account_id, row.token_hash)
    repo.audit(account.account_id, "completed")
    db.commit()
