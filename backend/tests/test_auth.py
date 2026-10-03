"""Auth endpoint tests — UC01 register, UC02 login, token handling."""

from datetime import datetime, timedelta, timezone

from jose import jwt


def _register(client, email="learner@test.dev", password="Secret123!", name="Le"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
            "password_confirm": password,
        },
    )


def _login(client, email="learner@test.dev", password="Secret123!"):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )


def test_register_success(client):
    r = _register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "learner@test.dev"
    assert body["roles"] == ["Learner"]
    assert body["status"] == "active"


def test_register_duplicate_email(client):
    assert _register(client).status_code == 201
    r = _register(client)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "email_taken"


def test_register_password_mismatch(client):
    r = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Le",
            "email": "a@b.dev",
            "password": "Secret123!",
            "password_confirm": "different",
        },
    )
    assert r.status_code == 422


def test_register_short_password(client):
    r = _register(client, password="short")
    assert r.status_code == 422


def test_register_invalid_email(client):
    r = _register(client, email="not-an-email")
    assert r.status_code == 422


def test_login_success(client):
    _register(client)
    r = _login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["account"]["roles"] == ["Learner"]


def test_login_wrong_password(client):
    _register(client)
    r = _login(client, password="WrongPass1!")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_credentials"


def test_login_unknown_email(client):
    r = _login(client, email="ghost@test.dev")
    assert r.status_code == 401


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_me_with_token(client):
    _register(client)
    token = _login(client).json()["access_token"]
    r = client.get("/api/v1/auth/me", headers=_bearer(token))
    assert r.status_code == 200
    assert r.json()["email"] == "learner@test.dev"


def test_me_without_token(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "missing_token"


def test_me_malformed_token(client):
    r = client.get("/api/v1/auth/me", headers=_bearer("not.a.jwt"))
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_token"


def test_me_expired_token(client):
    _register(client)
    token = _login(client).json()["access_token"]
    payload = jwt.get_unverified_claims(token)
    payload["exp"] = datetime.now(timezone.utc) - timedelta(minutes=1)
    expired = jwt.encode(payload, "test-secret-not-for-production", algorithm="HS256")
    r = client.get("/api/v1/auth/me", headers=_bearer(expired))
    assert r.status_code == 401
