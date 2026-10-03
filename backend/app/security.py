"""Password hashing (bcrypt) and JWT issuing/verification.

NOTE: requirements.txt previously listed passlib, which is unmaintained and
broken with bcrypt 5.x (its self-test crashes on the >72-byte check). We use
the bcrypt library directly — it is maintained and already installed via the
passlib extra. Passwords are capped at 72 bytes by DTO validation.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from .config import Settings
from .errors import AppError


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(
    account_id: int, roles: list[str], settings: Settings
) -> tuple[str, int]:
    """Returns (token, expires_in_seconds)."""
    expires_in = settings.access_token_expire_minutes * 60
    now = datetime.now(timezone.utc)
    payload = {
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
    if not payload.get("sub"):
        raise AppError(401, "invalid_token", "Token is missing the subject claim")
    return payload
