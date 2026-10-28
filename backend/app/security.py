"""Password hashing (bcrypt) and JWT issuing/verification.

NOTE: requirements.txt previously listed passlib, which is unmaintained and
broken with bcrypt 5.x (its self-test crashes on the >72-byte check). We use
the bcrypt library directly as a maintained runtime dependency.
Passwords are capped at 72 bytes by DTO validation.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from jwt import PyJWTError as JWTError

from .config import Settings
from .errors import AppError


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def credential_epoch(value: datetime | None) -> int:
    """Exact microseconds since the epoch; 0 means no password change known."""
    if value is None:
        return 0
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    delta = value - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds


def create_access_token(
    account_id: int,
    roles: list[str],
    settings: Settings,
    *,
    auth_time: int | None = None,
    password_changed_at: datetime | None = None,
) -> tuple[str, int]:
    """Returns (token, expires_in_seconds)."""
    expires_in = settings.access_token_expire_minutes * 60
    now = datetime.now(timezone.utc)
    auth_time = auth_time if auth_time is not None else int(now.timestamp())
    remaining = auth_time + settings.access_session_max_minutes * 60 - int(now.timestamp())
    if remaining <= 0:
        raise AppError(401, "reauthentication_required", "Please sign in again to continue")
    expires_in = min(expires_in, remaining)
    payload = {
        "typ": "access",
        "auth_time": auth_time,
        # Compared against account.password_changed_at on every request, so a
        # password reset invalidates all previously issued sessions.
        "pwd_at": credential_epoch(password_changed_at),
        "sub": str(account_id),
        "roles": roles,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), expires_in


def decode_access_token(token: str, settings: Settings) -> dict:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        raise AppError(401, "invalid_token", "Token is invalid or expired")
    if payload.get("typ") != "access" or not payload.get("exp"):
        raise AppError(401, "invalid_token", "Token is not an expiring access token")
    if not payload.get("sub"):
        raise AppError(401, "invalid_token", "Token is missing the subject claim")
    return payload
