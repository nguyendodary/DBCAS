"""Rotating refresh JWTs with hashed persistence and family replay revocation."""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import delete, select, update

from ..errors import AppError
from ..models import RefreshSession
from ..repositories import AccountRepository
from ..schemas import TokenResponse
from ..security import create_access_token, credential_epoch
from .auth_service import to_summary


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _revoke(db, family_id, now):
    db.execute(update(RefreshSession).where(RefreshSession.family_id == family_id,
               RefreshSession.revoked_at.is_(None)).values(revoked_at=now))


def _pair(db, account, settings, family_id, expires_at):
    now = datetime.now(timezone.utc)
    claims = {"typ": "refresh", "sub": str(account.account_id), "family": family_id,
              "pwd_at": credential_epoch(account.password_changed_at),
              "jti": secrets.token_urlsafe(32), "iat": now, "exp": expires_at}
    token = jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    db.add(RefreshSession(token_hash=digest(token), family_id=family_id,
                         account_id=account.account_id, credential_version=claims["pwd_at"],
                         created_at=now, expires_at=expires_at))
    access, seconds = create_access_token(account.account_id, sorted(r.role_name for r in account.roles),
                                         settings, password_changed_at=account.password_changed_at,
                                         session_family=family_id)
    return TokenResponse(access_token=access, expires_in=seconds, account=to_summary(account),
                         refresh_token=token, refresh_expires_in=max(0, int((expires_at - now).total_seconds())))


def issue(db, account_id, settings):
    account = AccountRepository(db).get_for_update(account_id)
    if account is None or account.status != "active":
        raise AppError(401, "invalid_credentials", "Account is not active")
    now = datetime.now(timezone.utc)
    db.execute(delete(RefreshSession).where(RefreshSession.account_id == account_id,
               RefreshSession.expires_at < now - timedelta(days=1)))
    pair = _pair(db, account, settings, uuid.uuid4().hex, now + timedelta(days=settings.refresh_token_expire_days))
    db.commit()
    return pair


def rotate(db, token, settings):
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm],
                            options={"require": ["exp", "iat", "sub", "jti", "family", "pwd_at"]})
        if claims.get("typ") != "refresh" or type(claims["pwd_at"]) is not int:
            raise ValueError("Invalid purpose")
        account_id = int(claims["sub"])
    except (jwt.PyJWTError, ValueError, TypeError):
        raise AppError(401, "invalid_refresh_token", "Refresh token is invalid or expired")
    # Account first is the shared lock order; concurrent refresh and role changes serialize.
    account = AccountRepository(db).get_for_update(account_id)
    row = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == digest(token)).with_for_update())
    now = datetime.now(timezone.utc)
    if row is None or row.account_id != account_id or row.family_id != claims["family"]:
        raise AppError(401, "invalid_refresh_token", "Refresh token is invalid or expired")
    if (row.consumed_at is not None or row.revoked_at is not None or row.expires_at <= now
            or account is None or account.status != "active"
            or row.credential_version != credential_epoch(account.password_changed_at)
            or claims["pwd_at"] != row.credential_version):
        _revoke(db, row.family_id, now)
        # Revocation must survive the HTTP error handler's transaction rollback.
        db.commit()
        raise AppError(401, "invalid_refresh_token", "Refresh session has been revoked; sign in again")
    row.consumed_at = now
    pair = _pair(db, account, settings, row.family_id, row.expires_at)
    db.commit()
    return pair


def revoke(db, token):
    row = db.get(RefreshSession, digest(token))
    if row is None:
        return
    AccountRepository(db).get_for_update(row.account_id)
    _revoke(db, row.family_id, datetime.now(timezone.utc))
    db.commit()
