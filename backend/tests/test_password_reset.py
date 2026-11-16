"""Self-service password recovery: request → emailed OTP → verify → confirm.

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
from app.models import (
    Account,
    AccountIdentity,
    PasswordResetAudit,
    PasswordResetOtp,
    PasswordResetToken,
)
from app.routers import auth as auth_router
from app.security import credential_epoch
from app.services import mail as mail_module
from app.services import oauth as oauth_service
from app.services import password_reset
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


def _verify(client, otp, email=KNOWN):
    return client.post(
        "/api/v1/auth/password-reset/verify", json={"email": email, "otp": otp}
    )


def _confirm(client, token, password=NEW, confirm=None):
    return client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": token,
            "password": password,
            "password_confirm": confirm if confirm is not None else password,
        },
    )


def _wrong(otp):
    """A syntactically valid code that differs from ``otp``."""
    return f"{(int(otp) + 1) % 1_000_000:06d}"


def _age_otp(db_session, seconds):
    """Pretend the live code was issued ``seconds`` ago (clears the cooldown)."""
    db_session.execute(
        update(PasswordResetOtp).values(
            requested_at=PasswordResetOtp.requested_at - timedelta(seconds=seconds),
            expires_at=PasswordResetOtp.expires_at - timedelta(seconds=seconds),
        )
    )
    db_session.commit()


class FakeMailer:
    configured = True

    def __init__(self):
        self.messages = []

    def send_password_reset_otp(self, email, otp, expires_minutes):
        self.messages.append({"email": email, "otp": otp, "minutes": expires_minutes})
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


def _issue(mail_client, mailer):
    """Register the known learner, request a code, return the emailed code."""
    assert _register(mail_client).status_code == 201
    assert _request(mail_client).status_code == 202
    return mailer.messages[-1]["otp"]


# --------------------------------------------------------------------- request


def test_request_for_unknown_email_is_generic_and_sends_nothing(
    mail_client, mailer, db_session
):
    r = _request(mail_client, "ghost@test.dev")
    assert r.status_code == 202
    assert r.json() == {"status": "accepted"}
    assert mailer.messages == []
    assert db_session.scalar(select(PasswordResetOtp)) is None
    assert db_session.scalar(select(PasswordResetToken)) is None


def test_request_for_known_email_emails_a_six_digit_code(
    mail_client, mailer, db_session
):
    assert _register(mail_client).status_code == 201
    r = _request(mail_client)
    assert r.status_code == 202
    assert r.json() == {"status": "accepted"}
    assert "otp" not in r.json()

    assert len(mailer.messages) == 1
    message = mailer.messages[0]
    assert message["email"] == KNOWN
    assert message["minutes"] == get_settings().password_reset_otp_ttl_minutes
    assert re.fullmatch(r"[0-9]{6}", message["otp"])

    stored = db_session.scalar(select(PasswordResetOtp))
    assert stored is not None
    assert stored.otp_hash == password_reset.hash_otp(
        stored.account_id, message["otp"], get_settings()
    )
    # Never the plaintext, and not a bare unkeyed hash of the code either.
    assert stored.otp_hash != message["otp"]
    assert stored.otp_hash != hashlib.sha256(message["otp"].encode()).hexdigest()
    assert stored.attempts == 0
    assert stored.expires_at > datetime.now(timezone.utc)
    # No reset token exists until the code is verified.
    assert db_session.scalar(select(PasswordResetToken)) is None
    events = db_session.scalars(select(PasswordResetAudit)).all()
    assert [e.event for e in events] == ["requested"]


def test_request_for_disabled_account_sends_nothing(mail_client, mailer, db_session):
    assert _register(mail_client).status_code == 201
    account = db_session.scalar(select(Account).where(Account.email == KNOWN))
    account.status = "disabled"
    db_session.commit()

    assert _request(mail_client).status_code == 202
    assert mailer.messages == []
    assert db_session.scalar(select(PasswordResetOtp)) is None


def test_resend_within_cooldown_sends_nothing_and_keeps_the_live_code(
    mail_client, mailer
):
    otp = _issue(mail_client, mailer)
    again = _request(mail_client)
    # Identical answer, no second email: the response reveals nothing.
    assert again.status_code == 202
    assert again.json() == {"status": "accepted"}
    assert len(mailer.messages) == 1
    assert _verify(mail_client, otp).status_code == 200


def test_resend_after_cooldown_replaces_the_code_and_resets_attempts(
    mail_client, mailer, db_session
):
    first = _issue(mail_client, mailer)
    assert _verify(mail_client, _wrong(first)).status_code == 400
    assert db_session.scalar(select(PasswordResetOtp)).attempts == 1

    _age_otp(db_session, get_settings().password_reset_otp_resend_cooldown_seconds + 1)
    assert _request(mail_client).status_code == 202
    assert len(mailer.messages) == 2
    second = mailer.messages[1]["otp"]

    db_session.expire_all()
    assert db_session.scalar(select(PasswordResetOtp)).attempts == 0
    if second != first:
        assert _verify(mail_client, first).status_code == 400
    assert _verify(mail_client, second).status_code == 200


def test_requests_are_rate_limited_per_email_and_ip(mail_client):
    for _ in range(5):
        assert _request(mail_client, "nobody@test.dev").status_code == 202
    limited = _request(mail_client, "nobody@test.dev")
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "password_reset_rate_limited"
    assert limited.headers.get("retry-after")
    # A different address is not affected by another key's window.
    assert _request(mail_client, "someone-else@test.dev").status_code == 202


# ---------------------------------------------------------------------- verify


def test_verify_exchanges_the_code_for_a_single_use_token(
    mail_client, mailer, db_session
):
    otp = _issue(mail_client, mailer)

    r = _verify(mail_client, otp)
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"reset_token"}
    token = body["reset_token"]

    # The code is spent; only the token's digest is stored.
    assert db_session.scalar(select(PasswordResetOtp)) is None
    stored = db_session.scalar(select(PasswordResetToken))
    assert stored.token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert stored.expires_at > datetime.now(timezone.utc)

    replay = _verify(mail_client, otp)
    assert replay.status_code == 400
    assert replay.json()["error"]["code"] == "invalid_otp"


def test_wrong_code_is_rejected_then_correct_code_still_works(
    mail_client, mailer, db_session
):
    otp = _issue(mail_client, mailer)

    r = _verify(mail_client, _wrong(otp))
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_otp"
    db_session.expire_all()
    assert db_session.scalar(select(PasswordResetOtp)).attempts == 1

    assert _verify(mail_client, otp).status_code == 200


def test_fifth_wrong_guess_burns_the_code(mail_client, mailer, db_session):
    otp = _issue(mail_client, mailer)
    wrong = _wrong(otp)
    for _ in range(get_settings().password_reset_otp_max_attempts - 1):
        r = _verify(mail_client, wrong)
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "invalid_otp"

    last = _verify(mail_client, wrong)
    assert last.status_code == 429
    assert last.json()["error"]["code"] == "password_reset_rate_limited"
    db_session.expire_all()
    assert db_session.scalar(select(PasswordResetOtp)) is None

    # Even the right code no longer works - the user must start over.
    assert _verify(mail_client, otp).status_code in (400, 429)
    assert db_session.scalar(select(PasswordResetToken)) is None


def test_requesting_again_after_a_burnt_code_starts_fresh(mail_client, mailer):
    otp = _issue(mail_client, mailer)
    for _ in range(get_settings().password_reset_otp_max_attempts):
        _verify(mail_client, _wrong(otp))

    assert _request(mail_client).status_code == 202
    assert len(mailer.messages) == 2
    fresh = mailer.messages[1]["otp"]
    assert _verify(mail_client, fresh).status_code == 200


def test_unknown_email_follows_the_same_attempt_policy(mail_client):
    """No oracle: a ghost address answers exactly like a real account."""
    attempts = get_settings().password_reset_otp_max_attempts
    for _ in range(attempts - 1):
        r = _verify(mail_client, "123456", email="ghost@test.dev")
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "invalid_otp"
    last = _verify(mail_client, "123456", email="ghost@test.dev")
    assert last.status_code == 429
    assert last.json()["error"]["code"] == "password_reset_rate_limited"


def test_disabled_account_cannot_verify(mail_client, mailer, db_session):
    otp = _issue(mail_client, mailer)
    account = db_session.scalar(select(Account).where(Account.email == KNOWN))
    account.status = "disabled"
    db_session.commit()

    r = _verify(mail_client, otp)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_otp"
    assert db_session.scalar(select(PasswordResetToken)) is None


def test_expired_code_is_rejected(mail_client, mailer, db_session):
    otp = _issue(mail_client, mailer)
    _age_otp(db_session, get_settings().password_reset_otp_ttl_minutes * 60 + 5)

    r = _verify(mail_client, otp)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_otp"
    assert db_session.scalar(select(PasswordResetToken)) is None


def test_code_is_bound_to_its_account(mail_client, mailer):
    _register(mail_client, email="other@test.dev")
    _request(mail_client, "other@test.dev")
    other_otp = mailer.messages[0]["otp"]
    _register(mail_client)
    _request(mail_client)
    own_otp = mailer.messages[1]["otp"]

    if other_otp != own_otp:
        assert _verify(mail_client, other_otp).status_code == 400
    assert _verify(mail_client, own_otp).status_code == 200


@pytest.mark.parametrize(
    "otp", ["12345", "1234567", "12345a", "١٢٣٤٥٦", " 12345", "", "123 456"]
)
def test_verify_rejects_malformed_codes(mail_client, otp):
    assert _verify(mail_client, otp).status_code == 422


def test_verify_is_rate_limited_per_ip_across_addresses(mail_client):
    for i in range(get_settings().password_reset_ip_rate_limit_attempts):
        r = _verify(mail_client, "123456", email=f"ghost{i}@test.dev")
        assert r.status_code == 400
    limited = _verify(mail_client, "123456", email="another@test.dev")
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "password_reset_rate_limited"


def test_concurrent_verification_of_one_code_succeeds_exactly_once(
    mail_client, mailer
):
    otp = _issue(mail_client, mailer)

    def attempt():
        return _verify(TestClient(app), otp).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(lambda _: attempt(), range(2)))
    assert statuses == [200, 400]


# --------------------------------------------------------------------- confirm


def test_full_reset_changes_password_and_old_password_fails(
    mail_client, mailer, db_session
):
    otp = _issue(mail_client, mailer)
    token = _verify(mail_client, otp).json()["reset_token"]

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


def test_confirm_requires_a_token_minted_by_verify(mail_client, mailer):
    """The code alone, or any guessed value, cannot reach the password change."""
    otp = _issue(mail_client, mailer)
    for bogus in (otp, otp * 4, "x" * 43):
        r = _confirm(mail_client, bogus)
        assert r.status_code in (400, 422)
    assert _login(mail_client, password=OLD).status_code == 200


def test_reset_token_is_single_use(mail_client, mailer):
    otp = _issue(mail_client, mailer)
    token = _verify(mail_client, otp).json()["reset_token"]

    assert _confirm(mail_client, token).status_code == 200
    replay = _confirm(mail_client, token, password="Another789!")
    assert replay.status_code == 400
    assert replay.json()["error"]["code"] == "invalid_reset_token"


def test_expired_reset_token_is_rejected(mail_client, mailer, db_session):
    otp = _issue(mail_client, mailer)
    token = _verify(mail_client, otp).json()["reset_token"]
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


def test_a_second_verification_revokes_the_previous_token(mail_client, mailer):
    otp = _issue(mail_client, mailer)
    first = _verify(mail_client, otp).json()["reset_token"]

    # Verifying spent the code, so a fresh request is not subject to cooldown.
    assert _request(mail_client).status_code == 202
    second_otp = mailer.messages[-1]["otp"]
    second = _verify(mail_client, second_otp).json()["reset_token"]

    assert _confirm(mail_client, first).status_code == 400
    assert _confirm(mail_client, second).status_code == 200


def test_concurrent_redemption_succeeds_exactly_once(mail_client, mailer):
    otp = _issue(mail_client, mailer)
    token = _verify(mail_client, otp).json()["reset_token"]

    def attempt():
        return _confirm(TestClient(app), token).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(lambda _: attempt(), range(2)))
    assert statuses == [200, 400]


def test_password_policy_still_applies_on_confirm(mail_client, mailer):
    otp = _issue(mail_client, mailer)
    token = _verify(mail_client, otp).json()["reset_token"]

    assert _confirm(mail_client, token, password="short").status_code == 422
    assert (
        _confirm(mail_client, token, password=NEW, confirm="different").status_code
        == 422
    )
    # A rejected password does not burn the token.
    assert _confirm(mail_client, token).status_code == 200


def test_reset_invalidates_existing_sessions(mail_client, mailer):
    assert _register(mail_client).status_code == 201
    old_token = _login(mail_client).json()["access_token"]
    headers = {"Authorization": f"Bearer {old_token}"}
    assert mail_client.get("/api/v1/auth/me", headers=headers).status_code == 200

    _request(mail_client)
    token = _verify(mail_client, mailer.messages[0]["otp"]).json()["reset_token"]
    assert _confirm(mail_client, token).status_code == 200

    assert mail_client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert mail_client.post("/api/v1/auth/renew", headers=headers).status_code == 401

    fresh = _login(mail_client, password=NEW).json()["access_token"]
    assert mail_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {fresh}"}
    ).status_code == 200


# ------------------------------------------------------------ mail and config


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
            assert mailer.send_password_reset_otp(KNOWN, "482913", 10) is False
    finally:
        app.dependency_overrides.pop(auth_router.get_mailer, None)

    assert "Password reset email delivery failed" in caplog.text
    assert "482913" not in caplog.text
    assert KNOWN not in caplog.text
    otp_row = db_session.scalar(select(PasswordResetOtp))
    assert otp_row is not None
    assert len(otp_row.otp_hash) == 64


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
    otp = mailer.messages[0]["otp"]
    token = _verify(mail_client, otp, email="oauth-only@test.dev").json()["reset_token"]
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
    assert Mailer(settings).send_password_reset_otp("learner@test.dev", "482913", 10)

    message = sent["message"]
    assert message["To"] == "learner@test.dev"
    assert message["From"] == "DBCAS <no-reply@dbcas.local>"
    assert "Mã xác minh" in message["Subject"]
    body = message.get_content()
    assert "482913" in body
    assert "10" in body
    assert "password reset" in body
    assert "đặt lại mật khẩu" in body
    assert "http" not in body  # a code, not a link
