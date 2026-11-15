"""Self-service password recovery: request → emailed OTP → verify → confirm.

Flow: ``request`` emails a 6-digit one-time passcode; ``verify`` exchanges a
correct code for a short-lived single-use reset token; ``confirm`` redeems
that token to set the new password. The password change is therefore
enforced server-side - the page that collects a new password is useless
without a token only a verified code can mint.

Security invariants:

- Only a keyed HMAC-SHA256 digest of the code is persisted (a plain hash of
  a 6-digit number is brute-forceable from a database leak); the plaintext
  exists solely inside the email message. Reset tokens are stored as SHA-256
  digests of 256-bit random values.
- The request endpoint answers identically for unknown, disabled and known
  addresses, and the email is sent from a background task so SMTP latency
  does not reveal address existence through response timing. The verify
  endpoint answers unknown, disabled, expired and wrong-code cases with the
  same error.
- One live code per account: issuing replaces the previous one. A code dies
  on first success, on expiry, or after ``password_reset_otp_max_attempts``
  wrong guesses (the counter is committed before the error is raised).
- One live token per account: issuing revokes older unredeemed tokens, and
  a successful redemption burns its token and revokes the rest.
- The token row is locked FOR UPDATE before redemption, so two concurrent
  redemptions of the same token cannot both succeed.
- Resetting sets ``password_changed_at``; access tokens carry a matching
  ``pwd_at`` claim, which invalidates every session issued before the
  change. Password hashes use the existing bcrypt path.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..config import Settings
from ..errors import AppError
from ..repositories import AccountRepository, PasswordResetRepository, SecurityRepository
from ..schemas import PasswordResetConfirmRequest
from ..security import hash_password

_TOKEN_BYTES = 32
_OTP_DIGITS = 6


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_otp(account_id: int, otp: str, settings: Settings) -> str:
    """Keyed digest bound to the account, so equal codes never share a hash."""
    key = hashlib.sha256(
        b"dbcas:password-reset-otp:" + settings.jwt_secret.encode("utf-8")
    ).digest()
    return hmac.new(key, f"{account_id}:{otp}".encode("utf-8"), hashlib.sha256).hexdigest()


def _invalid_otp() -> AppError:
    return AppError(400, "invalid_otp", "This code is invalid or has expired")


def request_reset(db: Session, email: str, settings: Settings) -> tuple[str, str] | None:
    """Issue a code for an active account; None for anything else.

    Returns (plaintext_otp, account_email); the caller must deliver the
    message in a background task and must never log or return the code.
    Returns None without issuing when the previous code is younger than the
    resend cooldown, so a flood of requests cannot spam one mailbox.
    """
    account = AccountRepository(db).find_by_email(email)
    if account is None or account.status != "active":
        return None
    SecurityRepository(db).lock("password-reset:" + str(account.account_id))
    repo = PasswordResetRepository(db)
    repo.prune()
    repo.prune_otps()
    now = datetime.now(timezone.utc)
    live = repo.otp_for_update(account.account_id)
    if live is not None and (now - live.requested_at) < timedelta(
        seconds=settings.password_reset_otp_resend_cooldown_seconds
    ):
        db.commit()
        return None
    otp = f"{secrets.randbelow(10 ** _OTP_DIGITS):0{_OTP_DIGITS}d}"
    repo.store_otp(
        account.account_id,
        hash_otp(account.account_id, otp, settings),
        now,
        now + timedelta(minutes=settings.password_reset_otp_ttl_minutes),
    )
    repo.audit(account.account_id, "requested")
    db.commit()
    return otp, account.email


def verify_otp(db: Session, email: str, otp: str, settings: Settings) -> str:
    """Exchange a correct code for a single-use reset token (plaintext).

    Every failure raises the same ``invalid_otp`` error. A wrong guess is
    counted and committed before raising; the last permitted guess deletes
    the code so it can never be tried again.
    """
    account = AccountRepository(db).find_by_email(email)
    if account is None or account.status != "active":
        # Comparable CPU work for unknown/disabled accounts.
        hmac.compare_digest(hash_otp(0, otp, settings), "0" * 64)
        raise _invalid_otp()
    SecurityRepository(db).lock("password-reset:" + str(account.account_id))
    repo = PasswordResetRepository(db)
    row = repo.otp_for_update(account.account_id)
    now = datetime.now(timezone.utc)
    if row is None or row.expires_at <= now:
        if row is not None:
            repo.delete_otp(account.account_id)
        db.commit()
        raise _invalid_otp()
    if not hmac.compare_digest(hash_otp(account.account_id, otp, settings), row.otp_hash):
        row.attempts += 1
        if row.attempts >= settings.password_reset_otp_max_attempts:
            repo.delete_otp(account.account_id)
        db.commit()
        raise _invalid_otp()
    repo.delete_otp(account.account_id)
    token = secrets.token_urlsafe(_TOKEN_BYTES)
    repo.store_token(
        hash_reset_token(token),
        account.account_id,
        now + timedelta(minutes=settings.password_reset_token_ttl_minutes),
    )
    db.commit()
    return token


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
            400, "invalid_reset_token", "This reset session is invalid or has expired"
        )
    account = AccountRepository(db).get_for_update(row.account_id)
    if account is None or account.status != "active":
        raise AppError(
            400, "invalid_reset_token", "This reset session is invalid or has expired"
        )
    account.password_hash = hash_password(payload.password)
    account.password_set = True
    account.password_changed_at = now
    row.used_at = now
    repo.revoke_others(account.account_id, row.token_hash)
    repo.audit(account.account_id, "completed")
    db.commit()
