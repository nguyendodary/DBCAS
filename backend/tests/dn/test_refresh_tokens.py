"""Refresh replay, expiry, ownership and concurrent rotation on real PostgreSQL."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import select

from app.config import get_settings
from app.db import get_session_factory
from app.errors import AppError
from app.models import Account, RefreshSession
from app.services import refresh_tokens


def sign_in(client):
    payload = {"name": "DN Learner", "email": "dn-refresh@example.test",
               "password": "ExamplePass123!", "password_confirm": "ExamplePass123!"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    response = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert response.status_code == 200
    return response.json()


def refresh(client, token):
    return client.post("/api/v1/auth/refresh", json={"refresh_token": token})


def test_rotates_hashes_and_replay_revokes_family_and_access(client, db_session):
    pair = sign_in(client)
    row = db_session.scalar(select(RefreshSession))
    assert row.token_hash == refresh_tokens.digest(pair["refresh_token"])
    assert pair["refresh_token"] not in row.token_hash
    assert jwt.decode(pair["refresh_token"], get_settings().jwt_secret, algorithms=["HS256"])["typ"] == "refresh"
    rotated = refresh(client, pair["refresh_token"])
    assert rotated.status_code == 200
    new = rotated.json()
    assert new["refresh_token"] != pair["refresh_token"]
    assert new["refresh_expires_in"] <= pair["refresh_expires_in"]
    headers = {"Authorization": "Bearer " + new["access_token"]}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert refresh(client, pair["refresh_token"]).status_code == 401
    assert refresh(client, new["refresh_token"]).status_code == 401
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_logout_is_idempotent_and_revoke_survives_requests(client):
    pair = sign_in(client)
    payload = {"refresh_token": pair["refresh_token"]}
    assert client.post("/api/v1/auth/logout", json=payload).status_code == 204
    assert client.post("/api/v1/auth/logout", json=payload).status_code == 204
    assert refresh(client, pair["refresh_token"]).status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + pair["access_token"]}).status_code == 401


@pytest.mark.parametrize("change", ["credentials", "disabled", "expired"])
def test_rejects_invalidated_accounts_and_storage_expiry(client, db_session, change):
    pair = sign_in(client)
    row = db_session.scalar(select(RefreshSession))
    account = db_session.get(Account, pair["account"]["account_id"])
    if change == "credentials":
        account.password_changed_at = datetime.now(timezone.utc)
    elif change == "disabled":
        account.status = "disabled"
    else:
        row.created_at = datetime.now(timezone.utc) - timedelta(days=2)
        row.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()
    assert refresh(client, pair["refresh_token"]).status_code == 401


def test_access_refresh_purpose_separation_and_validation(client):
    pair = sign_in(client)
    assert refresh(client, pair["access_token"]).status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + pair["refresh_token"]}).status_code == 401
    assert refresh(client, "x" * 64).status_code == 401
    assert refresh(client, "x").status_code == 422


def test_concurrent_refresh_has_one_winner_and_revokes_replayed_family(client):
    pair = sign_in(client)
    def rotate(_):
        with get_session_factory()() as db:
            try:
                return refresh_tokens.rotate(db, pair["refresh_token"], get_settings())
            except AppError:
                return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(rotate, range(2)))
    winners = [r for r in results if r is not None]
    assert len(winners) == 1
    assert refresh(client, winners[0].refresh_token).status_code == 401
