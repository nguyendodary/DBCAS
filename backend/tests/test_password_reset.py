"""Self-service password recovery: request → emailed token → confirm.

The fake mailer captures what an SMTP relay would deliver; separate tests
exercise the real Mailer against a stubbed transport, and the browser E2E
gate verifies actual Mailpit delivery.
"""

import hashlib
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.config import Settings, get_settings
from app.main import app
from app.models import Account, AccountIdentity, PasswordResetAudit, PasswordResetToken
from app.routers import auth as auth_router
from app.security import credential_epoch
from app.services import mail as mail_module
from app.services import oauth as oauth_service
from app.services.mail import Mailer

KNOWN = "learner@test.dev"
OLD = "Secret123!"
NEW = "Changed456!"


def _register(client, email=KNOWN, password=OLD):
    return client.post(
        "/api/v1/auth/register",
        json={
            "name": "Le",
            "email": email,
            "password": password,
            "password_confirm": password,
        },
    )


def _login(client, email=KNOWN, password=OLD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def _request(client, email=KNOWN):
    return client.post("/api/v1/auth/password-reset/request", json={"email": email})


def _confirm(client, token, password=NEW, confirm=None):
    return client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": token,
            "password": password,
            "password_confirm": confirm if confirm is not None else password,
        },
    )


def _token_from(url):
    match = re.search(r"[?&]token=([A-Za-z0-9_-]+)", url)
    assert match, f"no token in reset link: {url}"
    return match.group(1)


class FakeMailer:
    configured = True

    def __init__(self):
        self.messages = []

    def send_password_reset(self, email, reset_url, expires_minutes):
        self.messages.append(
            {"email": email, "url": reset_url, "minutes": expires_minutes}
        )
        return True


@pytest.fixture()
def mailer():
    return FakeMailer()


@pytest.fixture()
def mail_client(client, mailer):
    app.dependency_overrides[auth_router.get_mailer] = lambda: mailer
    try:
        yield client
    finally:
        app.dependency_overrides.pop(auth_router.get_mailer, None)


def test_request_for_unknown_email_is_generic_and_sends_nothing(
    mail_client, mailer, db_session
):
    r = _request(mail_client, "ghost@test.dev")
    assert r.status_code == 202
    assert r.json() == {"status": "accepted"}
    assert mailer.messages == []
    assert db_session.scalar(select(PasswordResetToken)) is None


def test_request_for_known_email_emails_a_trusted_origin_link(
    mail_client, mailer, db_session
):
    assert _register(mail_client).status_code == 201
    r = _request(mail_client)
    assert r.status_code == 202
    assert r.json() == {"status": "accepted"}
    assert "token" not in r.json()

    assert len(mailer.messages) == 1
    message = mailer.messages[0]
    assert message["email"] == KNOWN
    assert message["minutes"] == get_settings().password_reset_token_ttl_minutes
    # The link origin is the configured frontend, never the request Host.
    assert message["url"].startswith(
        get_settings().frontend_url.rstrip("/") + "/reset-password?token="
    )
    token = _token_from(message["url"])

    stored = db_session.scalar(select(PasswordResetToken))
    assert stored is not None
    assert stored.token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert stored.token_hash != token
    assert stored.expires_at > datetime.now(timezone.utc)
    events = db_session.scalars(select(PasswordResetAudit)).all()
    assert [e.event for e in events] == ["requested"]


def test_request_for_disabled_account_sends_nothing(mail_client, mailer, db_session):
    assert _register(mail_client).status_code == 201
    account = db_session.scalar(select(Account).where(Account.email == KNOWN))
    account.status = "disabled"
    db_session.commit()

    assert _request(mail_client).status_code == 202
    assert mailer.messages == []


def test_full_reset_changes_password_and_old_password_fails(
    mail_client, mailer, db_session
):
    assert _register(mail_client).status_code == 201
    assert _request(mail_client).status_code == 202
    token = _token_from(mailer.messages[0]["url"])

    r = _confirm(mail_client, token)
    assert r.status_code == 200
    assert r.json() == {"status": "reset"}

    assert _login(mail_client, password=OLD).status_code == 401
    assert _login(mail_client, password=NEW).status_code == 200

    db_session.expire_all()
    account = db_session.scalar(select(Account).where(Account.email == KNOWN))
    assert account.password_set is True
    assert account.password_changed_at is not None
    events = db_session.scalars(
        select(PasswordResetAudit).order_by(PasswordResetAudit.audit_id)
    ).all()
    assert [e.event for e in events] == ["requested", "completed"]


def test_reset_token_is_single_use(mail_client, mailer):
    assert _register(mail_client).status_code == 201
    _request(mail_client)
    token = _token_from(mailer.messages[0]["url"])

    assert _confirm(mail_client, token).status_code == 200
    replay = _confirm(mail_client, token, password="Another789!")
    assert replay.status_code == 400
    assert replay.json()["error"]["code"] == "invalid_reset_token"


def test_expired_token_is_rejected(mail_client, mailer, db_session):
    assert _register(mail_client).status_code == 201
    _request(mail_client)
    token = _token_from(mailer.messages[0]["url"])
    db_session.execute(
        update(PasswordResetToken).values(
            requested_at=datetime.now(timezone.utc) - timedelta(minutes=20),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
    )
    db_session.commit()

    r = _confirm(mail_client, token)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_reset_token"


def test_invalid_token_is_rejected(mail_client):
    r = _confirm(mail_client, "x" * 43)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_reset_token"


def test_new_request_revokes_the_previous_token(mail_client, mailer):
    assert _register(mail_client).status_code == 201
    _request(mail_client)
    first = _token_from(mailer.messages[0]["url"])
    _request(mail_client)
    second = _token_from(mailer.messages[1]["url"])

    assert _confirm(mail_client, first).status_code == 400
    assert _confirm(mail_client, second).status_code == 200


def test_concurrent_redemption_succeeds_exactly_once(mail_client, mailer):
    assert _register(mail_client).status_code == 201
    assert _request(mail_client).status_code == 202
    token = _token_from(mailer.messages[0]["url"])

    def attempt():
        return _confirm(TestClient(app), token).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(lambda _: attempt(), range(2)))
    assert statuses == [200, 400]


def test_password_policy_still_applies_on_confirm(mail_client, mailer):
    assert _register(mail_client).status_code == 201
    _request(mail_client)
    token = _token_from(mailer.messages[0]["url"])

    assert _confirm(mail_client, token, password="short").status_code == 422
    assert (
        _confirm(mail_client, token, password=NEW, confirm="different").status_code
        == 422
    )


def test_requests_are_rate_limited_per_email_and_ip(mail_client):
    for _ in range(5):
        assert _request(mail_client, "nobody@test.dev").status_code == 202
    limited = _request(mail_client, "nobody@test.dev")
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "password_reset_rate_limited"
    assert limited.headers.get("retry-after")
    # A different address is not affected by another key's window.
    assert _request(mail_client, "someone-else@test.dev").status_code == 202


def test_reset_invalidates_existing_sessions(mail_client, mailer):
    assert _register(mail_client).status_code == 201
    old_token = _login(mail_client).json()["access_token"]
    headers = {"Authorization": f"Bearer {old_token}"}
    assert mail_client.get("/api/v1/auth/me", headers=headers).status_code == 200

    _request(mail_client)
    assert _confirm(mail_client, _token_from(mailer.messages[0]["url"])).status_code == 200

    assert mail_client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert mail_client.post("/api/v1/auth/renew", headers=headers).status_code == 401

    fresh = _login(mail_client, password=NEW).json()["access_token"]
    assert mail_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {fresh}"}
    ).status_code == 200


def test_mailer_failure_is_generic_and_never_logs_secrets(
    client, db_session, caplog, monkeypatch
):
    def broken(*args, **kwargs):
        raise OSError("relay down")

    monkeypatch.setattr(mail_module.smtplib, "SMTP", broken)
    settings = Settings(
        _env_file=None, smtp_host="127.0.0.1", smtp_from="DBCAS <no-reply@dbcas.local>"
    )
    app.dependency_overrides[auth_router.get_mailer] = lambda: Mailer(settings)
    try:
        assert _register(client).status_code == 201
        with caplog.at_level(logging.WARNING):
            r = _request(client)
        assert r.status_code == 202
        assert r.json() == {"status": "accepted"}

        mailer = Mailer(settings)
        with caplog.at_level(logging.WARNING):
            assert (
                mailer.send_password_reset(
                    KNOWN, "http://localhost:5173/reset-password?token=known-secret-token", 15
                )
                is False
            )
    finally:
        app.dependency_overrides.pop(auth_router.get_mailer, None)

    assert "Password reset email delivery failed" in caplog.text
    assert "known-secret-token" not in caplog.text
    assert KNOWN not in caplog.text
    token_row = db_session.scalar(select(PasswordResetToken))
    assert token_row is not None
    assert len(token_row.token_hash) == 64


def test_unconfigured_smtp_reports_unavailable(client):
    assert _register(client).status_code == 201
    r = _request(client)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "password_reset_unavailable"


def test_oauth_only_account_gains_password_only_through_explicit_reset(
    mail_client, mailer, db_session
):
    ident = oauth_service.ProviderIdentity(
        provider="google",
        provider_user_id="oauth-new-user-1",
        email="oauth-only@test.dev",
        email_verified=True,
        name="OAuth User",
    )
    account = oauth_service.resolve_or_create(db_session, ident)
    assert account.password_set is False
    account_id = account.account_id

    assert _request(mail_client, "oauth-only@test.dev").status_code == 202
    token = _token_from(mailer.messages[0]["url"])
    assert _confirm(mail_client, token).status_code == 200

    db_session.expire_all()
    refreshed = db_session.get(Account, account_id)
    assert refreshed.password_set is True
    assert _login(mail_client, email="oauth-only@test.dev", password=NEW).status_code == 200
    # The social identity link is untouched by the reset.
    identities = db_session.scalars(
        select(AccountIdentity).where(AccountIdentity.account_id == account_id)
    ).all()
    assert len(identities) == 1


def test_credential_epoch_is_exact_microseconds():
    value = datetime(2026, 10, 28, 12, 0, 0, 123456, tzinfo=timezone.utc)
    assert credential_epoch(None) == 0
    assert credential_epoch(value) == int(value.timestamp() * 1_000_000)
    assert credential_epoch(value) % 1_000_000 == 123456


def test_mailer_builds_bilingual_plain_text(monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            self.host, self.port = host, port

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def starttls(self):
            pass

        def login(self, username, password):
            pass

        def send_message(self, message):
            sent["message"] = message

    monkeypatch.setattr(
        mail_module.smtplib,
        "SMTP",
        lambda host, port, timeout=None: FakeSMTP(host, port, timeout),
    )
    settings = Settings(
        _env_file=None,
        smtp_host="127.0.0.1",
        smtp_port=1026,
        smtp_from="DBCAS <no-reply@dbcas.local>",
    )
    assert Mailer(settings).send_password_reset(
        "learner@test.dev", "http://localhost:5173/reset-password?token=abc123", 15
    )

    message = sent["message"]
    assert message["To"] == "learner@test.dev"
    assert message["From"] == "DBCAS <no-reply@dbcas.local>"
    assert "Đặt lại mật khẩu" in message["Subject"]
    body = message.get_content()
    assert "http://localhost:5173/reset-password?token=abc123" in body
    assert "15" in body
    assert "password reset" in body
    assert "đặt lại mật khẩu" in body
