"""Authenticated, persistent account settings, scoped to the current user."""
import base64
import binascii
import struct

from ..errors import AppError
from ..repositories import AccountRepository
from ..schemas import TokenResponse
from ..security import hash_password, verify_password, create_access_token
from .auth_service import to_summary


def _account(db, account_id):
    account = AccountRepository(db).get_for_update(account_id)
    if account is None or account.status != "active":
        raise AppError(403, "account_disabled", "Account is unavailable")
    return account


def change_password(db, account_id, payload, settings):
    account = _account(db, account_id)
    if not verify_password(payload.current_password, account.password_hash):
        raise AppError(422, "current_password_incorrect", "Current password is incorrect")
    if verify_password(payload.new_password, account.password_hash):
        raise AppError(422, "password_unchanged", "Choose a different password")
    account.password_hash = hash_password(payload.new_password)
    account.token_version = (account.token_version or 0) + 1
    token, expires = create_access_token(account_id, sorted(r.role_name for r in account.roles), settings,
                                         token_version=account.token_version)
    db.commit()
    return TokenResponse(access_token=token, expires_in=expires, account=to_summary(account))


def validate_avatar(value):
    if value is None:
        return
    prefix = "data:image/png;base64,"
    if not value.startswith(prefix):
        raise AppError(422, "invalid_avatar", "The avatar must be a PNG image")
    try:
        raw = base64.b64decode(value[len(prefix):], validate=True)
        if (not 45 <= len(raw) <= 300000 or raw[:8] != b"\x89PNG\r\n\x1a\n"
                or raw[12:16] != b"IHDR" or raw[-12:] != b"\x00\x00\x00\x00IEND\xaeB`\x82"):
            raise ValueError()
        width, height = struct.unpack(">II", raw[16:24])
        if not (0 < width <= 512 and 0 < height <= 512):
            raise ValueError()
    except (ValueError, binascii.Error, struct.error):
        raise AppError(422, "invalid_avatar", "The avatar image is invalid or too large")


def save_avatar(db, account_id, value):
    validate_avatar(value)
    account = _account(db, account_id)
    account.avatar_data_url = value
    db.commit()
    return to_summary(account)
