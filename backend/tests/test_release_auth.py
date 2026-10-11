"""Production fail-closed configuration and token boundary regressions."""
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt
from pydantic import ValidationError

from app.config import Settings
from app.errors import AppError
from app.security import create_access_token, decode_access_token
from app.services import auth_service
from tests.test_auth import _login


def production_config(**overrides):
    values = dict(
        deployment_mode="production", jwt_secret="7c9fa73150c3469ebf0837aefae77d75c9b5e098bb46f17e",
        database_url="postgresql://app:K7p9m3Jx8s2Vw6Qz@db:5432/dbcas",
        sandbox_url="postgresql://learner_ro:R8t2Qw9f3Xc7Vb4N@sandbox:5432/postgres",
        sandbox_admin_url="postgresql://setup:S4w8Zq2E9r6Yt3Lu@sandbox:5432/postgres",
        frontend_url="https://dbcas.example.edu", cors_origins=["https://dbcas.example.edu"],
    )
    values.update(overrides)
    return values


def test_development_allows_local_defaults():
    assert Settings(_env_file=None, deployment_mode="development").deployment_mode == "development"


def test_safe_production_configuration_accepted():
    assert Settings(_env_file=None, **production_config()).deployment_mode == "production"


@pytest.mark.parametrize("secret", ["change_me_jwt_secret", "", "replace-with-production-secret-please", "your-secret-" * 4])
def test_production_rejects_unsafe_secret_without_disclosing_it(secret):
    with pytest.raises(ValidationError) as err:
        Settings(_env_file=None, **production_config(jwt_secret=secret))
    assert "Unsafe JWT_SECRET" in str(err.value)
    if secret:
        assert secret not in str(err.value)


@pytest.mark.parametrize("field", ["database_url", "sandbox_url", "sandbox_admin_url"])
def test_production_rejects_default_database_credentials(field):
    with pytest.raises(ValidationError, match="non-default database password"):
        Settings(_env_file=None, **production_config(**{field: "postgresql://postgres:test@unsafe:5432/db"}))


def test_production_rejects_shared_database_server():
    with pytest.raises(ValidationError, match="distinct PostgreSQL servers"):
        Settings(_env_file=None, **production_config(sandbox_url="postgresql://ro:R8t2Qw9f3Xc7Vb4N@db:5432/other"))


def test_production_requires_https_and_explicit_cors():
    with pytest.raises(ValidationError, match="HTTPS"):
        Settings(_env_file=None, **production_config(cors_origins=["*"]))


def test_access_decoder_accepts_issued_access_token():
    settings = Settings(_env_file=None, jwt_secret="isolated-test-signing-secret")
    token, _ = create_access_token(1, ["Learner"], settings)
    assert decode_access_token(token, settings)["typ"] == "access"


@pytest.mark.parametrize("purpose", ["oauth_handoff", "oauth_state", None])
def test_access_decoder_rejects_other_token_purposes(purpose):
    settings = Settings(_env_file=None, jwt_secret="isolated-test-signing-secret")
    token = jwt.encode({"sub": "1", "typ": purpose, "exp": datetime.now(timezone.utc) + timedelta(minutes=1)}, settings.jwt_secret, algorithm="HS256")
    with pytest.raises(AppError) as err:
        decode_access_token(token, settings)
    assert err.value.status_code == 401


def test_unknown_account_performs_password_verification(client, monkeypatch):
    seen = []
    original = auth_service.verify_password
    def verify(password, hashed):
        seen.append(hashed)
        return original(password, hashed)
    monkeypatch.setattr(auth_service, "verify_password", verify)
    assert _login(client, email="unknown@timing.test").status_code == 401
    assert len(seen) == 1
    assert seen[0].startswith("$2")
