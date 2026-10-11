"""OAuth sign-in tests — Google + GitHub authorization-code flows.

Provider HTTP is fully mocked through httpx.MockTransport injected via the
get_http_client dependency — the suite never touches the real providers.
The flow runs through the real TestClient cookie jar so the state/PKCE/
handoff cookie plumbing is verified end to end.
"""

from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from sqlalchemy import text

from app.config import get_settings
from app.main import app
from app.routers import oauth as oauth_router

GOOGLE_PROFILE = {
    "sub": "g-123",
    "email": "learner@test.dev",
    "email_verified": True,
    "name": "Le Learner",
}
GITHUB_USER = {"id": 777, "login": "lelearner", "name": "Le Learner", "email": None}
GITHUB_EMAILS = [
    {"email": "backup@test.dev", "primary": False, "verified": True},
    {"email": "gh-learner@test.dev", "primary": True, "verified": True},
]


@pytest.fixture()
def oauth_config():
    """Point the cached settings at fake provider registrations."""
    s = get_settings()
    keys = (
        "google_client_id", "google_client_secret", "google_redirect_uri",
        "github_client_id", "github_client_secret", "github_redirect_uri",
        "frontend_url",
    )
    saved = {k: getattr(s, k) for k in keys}
    s.google_client_id = "google-id"
    s.google_client_secret = "google-secret"
    s.google_redirect_uri = "http://localhost:5173/api/v1/auth/oauth/google/callback"
    s.github_client_id = "github-id"
    s.github_client_secret = "github-secret"
    s.github_redirect_uri = "http://localhost:5173/api/v1/auth/oauth/github/callback"
    s.frontend_url = "http://localhost:5173"
    yield s
    for k, v in saved.items():
        setattr(s, k, v)


def mock_provider_client(**routes):
    """httpx client backed by MockTransport; routes maps URL suffix →
    (status, json) or a callable taking the request."""

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        for suffix, spec in routes.items():
            if url.startswith(suffix):
                if callable(spec):
                    return spec(request)
                status, body = spec
                return httpx.Response(status, json=body)
        return httpx.Response(404, json={"error": "unmocked " + url})

    return httpx.Client(transport=httpx.MockTransport(handler), timeout=5.0)


@pytest.fixture()
def use_mock_http():
    """Swap the HTTP dependency per test; clears overrides afterwards."""
    def _set(client):
        app.dependency_overrides[oauth_router.get_http_client] = lambda: client
    yield _set
    app.dependency_overrides.pop(oauth_router.get_http_client, None)


def _google_client(**overrides):
    routes = {
        "https://oauth2.googleapis.com/token": (200, {"access_token": "g-tok"}),
        "https://openidconnect.googleapis.com/v1/userinfo": (200, GOOGLE_PROFILE),
    }
    routes.update(overrides)
    return mock_provider_client(**routes)


def _github_client(user=None, emails=None, token_error=None):
    routes = {}
    if token_error:
        routes["https://github.com/login/oauth/access_token"] = token_error
    else:
        routes["https://github.com/login/oauth/access_token"] = (
            200, {"access_token": "gh-tok"})
    routes["https://api.github.com/user/emails"] = (
        200, GITHUB_EMAILS if emails is None else emails)
    routes["https://api.github.com/user"] = (
        200, GITHUB_USER if user is None else user)
    return mock_provider_client(**routes)


def _start(client, provider):
    """Return (state, response) from a real /start call."""
    r = client.get(f"/api/v1/auth/oauth/{provider}/start", follow_redirects=False)
    assert r.status_code == 302
    qs = parse_qs(urlparse(r.headers["location"]).query)
    return qs["state"][0], r


def _callback(client, provider, state, code="authcode"):
    return client.get(
        f"/api/v1/auth/oauth/{provider}/callback?code={code}&state={state}",
        follow_redirects=False,
    )


def _error_code(response):
    return parse_qs(urlparse(response.headers["location"]).query).get(
        "oauth_error", [None])[0]


def _identity_count(db):
    return db.execute(text("SELECT COUNT(*) FROM account_identity")).scalar()


def _register(client, email="learner@test.dev", password="Secret123!", name="Le"):
    return client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email,
              "password": password, "password_confirm": password},
    )


# ---------- providers endpoint ----------


def test_providers_lists_both_configured(client, oauth_config):
    r = client.get("/api/v1/auth/oauth/providers")
    assert r.status_code == 200
    providers = {p["name"]: p["configured"] for p in r.json()["providers"]}
    assert providers == {"google": True, "github": True}


def test_providers_report_unconfigured(client, oauth_config):
    oauth_config.google_client_id = ""
    providers = {p["name"]: p["configured"]
                 for p in client.get("/api/v1/auth/oauth/providers").json()["providers"]}
    assert providers["google"] is False
    assert providers["github"] is True


def test_start_unconfigured_returns_503(client, oauth_config):
    oauth_config.google_client_id = ""
    r = client.get("/api/v1/auth/oauth/google/start", follow_redirects=False)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "oauth_not_configured"


def test_unknown_provider_404(client):
    r = client.get("/api/v1/auth/oauth/twitter/start", follow_redirects=False)
    assert r.status_code == 404


# ---------- Google ----------


def test_google_start_redirects_with_state_and_pkce(client, oauth_config):
    r = client.get("/api/v1/auth/oauth/google/start", follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers["location"]
    assert loc.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    qs = parse_qs(urlparse(loc).query)
    assert qs["client_id"] == ["google-id"]
    assert qs["redirect_uri"] == [oauth_config.google_redirect_uri]
    assert qs["response_type"] == ["code"]
    assert qs["scope"] == ["openid email profile"]
    assert qs["state"]
    assert qs["code_challenge"]
    assert qs["code_challenge_method"] == ["S256"]
    # the state is also bound to this browser via an HttpOnly cookie
    assert client.cookies.get("dbcas_oauth_state") == qs["state"][0]


def test_google_callback_creates_learner_and_handoff(
        client, oauth_config, use_mock_http, db_session):
    use_mock_http(_google_client())
    state, _ = _start(client, "google")
    r = _callback(client, "google", state)
    assert r.status_code == 302
    assert r.headers["location"] == "http://localhost:5173/auth/callback"
    assert client.cookies.get("dbcas_oauth_handoff")

    r2 = client.post("/api/v1/auth/oauth/complete")
    assert r2.status_code == 200
    body = r2.json()
    assert body["access_token"]
    assert body["account"]["email"] == "learner@test.dev"
    assert body["account"]["roles"] == ["Learner"]
    assert body["account"]["status"] == "active"

    assert _identity_count(db_session) == 1
    row = db_session.execute(
        text("SELECT provider, provider_user_id, provider_email, email_verified "
             "FROM account_identity")).fetchone()
    assert row == ("google", "g-123", "learner@test.dev", True)


def test_google_callback_invalid_state(client, oauth_config, use_mock_http):
    use_mock_http(_google_client())
    # no /start → no state cookie at all
    r = _callback(client, "google", "forged-state")
    assert r.status_code == 302
    assert _error_code(r) == "state"

    _start(client, "google")
    r = _callback(client, "google", "tampered-state")
    assert _error_code(r) == "state"


def test_google_callback_provider_denied(client, oauth_config):
    _start(client, "google")
    r = client.get(
        "/api/v1/auth/oauth/google/callback?error=access_denied",
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert _error_code(r) == "denied"


def test_google_unverified_email_never_links(
        client, oauth_config, use_mock_http, db_session):
    _register(client, email="victim@test.dev")
    profile = dict(GOOGLE_PROFILE, email="victim@test.dev", email_verified=False)
    use_mock_http(_google_client(**{
        "https://openidconnect.googleapis.com/v1/userinfo": (200, profile)}))
    state, _ = _start(client, "google")
    r = _callback(client, "google", state)
    assert _error_code(r) == "email_unverified"
    assert _identity_count(db_session) == 0


def test_google_verified_email_links_existing_account(
        client, oauth_config, use_mock_http, db_session):
    _register(client, email="learner@test.dev")
    use_mock_http(_google_client())
    state, _ = _start(client, "google")
    r = _callback(client, "google", state)
    assert r.headers["location"].endswith("/auth/callback")
    r2 = client.post("/api/v1/auth/oauth/complete")
    assert r2.status_code == 200
    # the registered account got the link — not a duplicate account
    count = db_session.execute(
        text("SELECT COUNT(*) FROM account WHERE email = 'learner@test.dev'")).scalar()
    assert count == 1
    assert _identity_count(db_session) == 1


def test_google_oauth_cannot_escalate_roles(
        client, oauth_config, use_mock_http):
    use_mock_http(_google_client())
    state, _ = _start(client, "google")
    _callback(client, "google", state)
    body = client.post("/api/v1/auth/oauth/complete").json()
    assert body["account"]["roles"] == ["Learner"]


def test_google_oauth_login_to_disabled_account_fails(
        client, oauth_config, use_mock_http, db_session):
    _register(client, email="learner@test.dev")
    db_session.execute(
        text("UPDATE account SET status = 'disabled' WHERE email = 'learner@test.dev'"))
    db_session.commit()
    use_mock_http(_google_client())
    state, _ = _start(client, "google")
    r = _callback(client, "google", state)
    assert _error_code(r) == "account_disabled"


def test_google_identity_reuse_logs_back_in(
        client, oauth_config, use_mock_http):
    use_mock_http(_google_client())
    state, _ = _start(client, "google")
    _callback(client, "google", state)
    client.post("/api/v1/auth/oauth/complete")
    # second flow for the same provider identity → same account, no dup link
    state, _ = _start(client, "google")
    _callback(client, "google", state)
    r = client.post("/api/v1/auth/oauth/complete")
    assert r.status_code == 200
    assert r.json()["account"]["email"] == "learner@test.dev"


# ---------- GitHub ----------


def test_github_start_redirects_with_state(client, oauth_config):
    r = client.get("/api/v1/auth/oauth/github/start", follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers["location"]
    assert loc.startswith("https://github.com/login/oauth/authorize?")
    qs = parse_qs(urlparse(loc).query)
    assert qs["client_id"] == ["github-id"]
    assert qs["redirect_uri"] == [oauth_config.github_redirect_uri]
    assert qs["scope"] == ["read:user user:email"]
    assert qs["state"]
    assert "code_challenge" not in qs
    assert client.cookies.get("dbcas_oauth_state") == qs["state"][0]


def test_github_callback_uses_verified_primary_email(
        client, oauth_config, use_mock_http, db_session):
    """Public email is null (private) → the /user/emails fallback picks the
    verified primary one."""
    use_mock_http(_github_client())
    state, _ = _start(client, "github")
    r = _callback(client, "github", state)
    assert r.status_code == 302
    assert r.headers["location"].endswith("/auth/callback")
    r2 = client.post("/api/v1/auth/oauth/complete")
    assert r2.status_code == 200
    assert r2.json()["account"]["email"] == "gh-learner@test.dev"
    assert r2.json()["account"]["roles"] == ["Learner"]
    row = db_session.execute(
        text("SELECT provider, provider_user_id FROM account_identity")).fetchone()
    assert row == ("github", "777")


def test_github_callback_invalid_state(client, oauth_config, use_mock_http):
    use_mock_http(_github_client())
    r = _callback(client, "github", "forged-state")
    assert _error_code(r) == "state"


def test_github_no_verified_email_rejected(
        client, oauth_config, use_mock_http, db_session):
    unverified = [{"email": "shady@test.dev", "primary": True, "verified": False}]
    use_mock_http(_github_client(emails=unverified))
    state, _ = _start(client, "github")
    r = _callback(client, "github", state)
    assert _error_code(r) == "email_unverified"
    assert _identity_count(db_session) == 0


def test_github_verified_email_links_existing_account(
        client, oauth_config, use_mock_http, db_session):
    _register(client, email="gh-learner@test.dev")
    use_mock_http(_github_client())
    state, _ = _start(client, "github")
    _callback(client, "github", state)
    r = client.post("/api/v1/auth/oauth/complete")
    assert r.status_code == 200
    count = db_session.execute(
        text("SELECT COUNT(*) FROM account WHERE email = 'gh-learner@test.dev'")).scalar()
    assert count == 1
    assert _identity_count(db_session) == 1


def test_github_oauth_cannot_escalate_roles(client, oauth_config, use_mock_http):
    """Even if the provider profile is hostile, new social accounts are
    always Learners — roles never come from provider data."""
    user = dict(GITHUB_USER, login="definitely-admin", name="Admin")
    use_mock_http(_github_client(user=user))
    state, _ = _start(client, "github")
    _callback(client, "github", state)
    body = client.post("/api/v1/auth/oauth/complete").json()
    assert body["account"]["roles"] == ["Learner"]


def test_github_exchange_failure(client, oauth_config, use_mock_http):
    use_mock_http(_github_client(
        token_error=(400, {"error": "bad_verification_code"})))
    state, _ = _start(client, "github")
    r = _callback(client, "github", state)
    assert _error_code(r) == "exchange"


# ---------- handoff ----------


def test_complete_without_handoff_is_401(client):
    r = client.post("/api/v1/auth/oauth/complete")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "oauth_handoff_invalid"


def test_handoff_is_single_use(client, oauth_config, use_mock_http):
    use_mock_http(_google_client())
    state, _ = _start(client, "google")
    _callback(client, "google", state)
    assert client.post("/api/v1/auth/oauth/complete").status_code == 200
    # replaying the same handoff (cookie already consumed/cleared → 401)
    assert client.post("/api/v1/auth/oauth/complete").status_code == 401


def test_oauth_token_then_calls_api(client, oauth_config, use_mock_http):
    """The token issued after social sign-in is a normal DBCAS JWT."""
    use_mock_http(_google_client())
    state, _ = _start(client, "google")
    _callback(client, "google", state)
    body = client.post("/api/v1/auth/oauth/complete").json()
    token = body["access_token"]
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "learner@test.dev"