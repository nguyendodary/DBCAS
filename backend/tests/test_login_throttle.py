"""Login rate limiting — brute-force resistance on UC02.

Design under test: a per-(email, client_ip) sliding-window counter of
``invalid_credentials`` failures. After ``login_rate_limit_attempts``
failures inside ``login_rate_limit_window_seconds``, the endpoint answers
429 (with ``Retry-After``) *before* verifying credentials; a successful
login resets the key's window. Time is controlled by injecting a fake
clock through the ``get_login_throttle`` dependency — no real sleeps.
"""

import pytest

from app.config import get_settings
from app.errors import AppError
from app.main import app
from app.services.login_throttle import LoginThrottle, get_login_throttle
from tests.test_auth import _login, _register

WINDOW = 300
LIMIT = 5


class FakeClock:
    def __init__(self):
        self.t = 1_000.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


@pytest.fixture()
def throttle():
    """Override the login-throttle dependency with a fake-clock instance."""
    t = LoginThrottle(now=FakeClock())
    app.dependency_overrides[get_login_throttle] = lambda: t
    yield t
    app.dependency_overrides.pop(get_login_throttle, None)


def _failures(client, n, email="learner@test.dev"):
    last = None
    for _ in range(n):
        last = _login(client, email=email, password="WrongPass1!")
    return last


def test_valid_login_still_works(client, throttle):
    _register(client)
    r = _login(client)
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_invalid_login_error_unchanged(client, throttle):
    _register(client)
    r = _login(client, password="WrongPass1!")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_credentials"


def test_repeated_failures_hit_429(client, throttle):
    _register(client)
    for _ in range(LIMIT):
        assert _login(client, password="WrongPass1!").status_code == 401
    r = _login(client, password="WrongPass1!")
    assert r.status_code == 429
    err = r.json()["error"]
    assert err["code"] == "login_rate_limited"
    assert int(r.headers["Retry-After"]) > 0


def test_threshold_boundary(client, throttle):
    """Attempts 1..LIMIT are 401; attempt LIMIT+1 is 429."""
    _register(client)
    for _ in range(LIMIT - 1):
        assert _login(client, password="WrongPass1!").status_code == 401
    assert _login(client, password="WrongPass1!").status_code == 401
    assert _login(client, password="WrongPass1!").status_code == 429


def test_429_rejects_even_correct_password(client, throttle):
    """A saturated window caps ALL attempts — throttle beats credentials."""
    _register(client)
    _failures(client, LIMIT)
    r = _login(client)  # correct password
    assert r.status_code == 429


def test_window_expiry_restores_access(client, throttle):
    _register(client)
    _failures(client, LIMIT)
    assert _login(client).status_code == 429
    throttle._now.advance(WINDOW + 1)
    r = _login(client)
    assert r.status_code == 200


def test_success_resets_failure_window(client, throttle):
    """A legit user is not punished for earlier typos."""
    _register(client)
    _failures(client, LIMIT - 1)
    assert _login(client).status_code == 200  # resets the counter
    _failures(client, LIMIT - 1)
    assert _login(client).status_code == 200


def test_disabled_account_does_not_count(client, throttle, db_session):
    """Valid credentials + disabled account → 403, not a throttle strike."""
    from app.repositories import AccountRepository

    _register(client, email="adm@t.dev")
    repo = AccountRepository(db_session)
    acct = repo.find_by_email("adm@t.dev")
    acct.status = "disabled"
    db_session.commit()
    for _ in range(LIMIT + 2):
        assert _login(client, email="adm@t.dev").status_code == 403
    # still 403 — never escalated to 429
    assert _login(client, email="adm@t.dev").status_code == 403


def test_identities_isolated(client, throttle):
    """Failures on email A never throttle email B (or admin A)."""
    _register(client, email="a@t.dev")
    _register(client, email="b@t.dev")
    _failures(client, LIMIT, email="a@t.dev")
    assert _login(client, email="a@t.dev").status_code == 429
    assert _login(client, email="b@t.dev").status_code == 200


def test_key_normalizes_email_case(client, throttle):
    """Case variants share one counter — no bypass by 'LEARNER@t.dev'."""
    _register(client)
    for _ in range(LIMIT):
        assert (
            _login(client, email="LEARNER@Test.dev", password="x").status_code
            == 401
        )
    assert _login(client, password="WrongPass1!").status_code == 429


def test_no_password_or_secret_leakage(client, throttle):
    _register(client)
    _failures(client, LIMIT + 1)
    for r in (
        _login(client, password="WrongPass1!"),
        _login(client),
    ):
        body = r.text
        assert "Secret123!" not in body
        assert "WrongPass1!" not in body
        assert "test-secret" not in body
        assert "password_hash" not in body


def test_jwt_issuance_unchanged(client, throttle):
    """The token contract stays identical when not throttled."""
    from jose import jwt

    _register(client)
    r = _login(client)
    claims = jwt.get_unverified_claims(r.json()["access_token"])
    assert set(claims) == {"sub", "roles", "iat", "exp"}
    assert claims["roles"] == ["Learner"]
    assert r.json()["expires_in"] == 3600
