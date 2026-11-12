"""Promotion of an existing demo database must fail closed."""
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.credential_policy import DEMO_ACCOUNT_PASSWORDS
from app.models import Account
from app.security import hash_password
from app.services.deployment_safety import validate_deployment_accounts


def deployment_settings(mode='production', **changes):
    values = dict(_env_file=None, deployment_mode=mode, jwt_secret='PrivateReleaseKey-' + 'x' * 40,
                  database_url='postgresql://app:PrivateDatabaseCredential123!@app-db:5432/dbcas',
                  sandbox_url='postgresql://learner:PrivateLearnerCredential123!@executor:5432/postgres',
                  sandbox_admin_url='postgresql://admin:PrivateSandboxCredential123!@executor:5432/postgres',
                  frontend_url='https://practice.example.edu', cors_origins=['https://practice.example.edu'],
                  smtp_host='', smtp_password='', google_client_secret='', github_client_secret='', llm_api_key='')
    values.update(changes)
    return Settings(**values)


@pytest.mark.parametrize('mode', ['staging', 'production'])
@pytest.mark.parametrize('status', ['active', 'disabled'])
@pytest.mark.parametrize('password', DEMO_ACCOUNT_PASSWORDS)
def test_existing_demo_account_blocks_promotion(db_session, mode, status, password):
    account = Account(email='legacy-demo@deployment.test', password_hash=hash_password(password), status=status)
    db_session.add(account)
    db_session.commit()
    with pytest.raises(RuntimeError, match='Unsafe development account credentials'):
        validate_deployment_accounts(db_session, deployment_settings(mode))
    assert db_session.get(Account, account.account_id).password_hash == account.password_hash


@pytest.mark.parametrize('password', DEMO_ACCOUNT_PASSWORDS)
def test_development_keeps_demo_accounts_usable(db_session, password):
    db_session.add(Account(email='demo@deployment.test', password_hash=hash_password(password)))
    db_session.commit()
    validate_deployment_accounts(db_session, SimpleNamespace(deployment_mode='development'))


@pytest.mark.parametrize('mode', ['staging', 'production'])
def test_rotated_account_allows_promotion(db_session, mode):
    db_session.add(Account(email='rotated@deployment.test', password_hash=hash_password('RotatedPrivate123!')))
    db_session.commit()
    validate_deployment_accounts(db_session, deployment_settings(mode))


@pytest.mark.parametrize('mode', ['staging', 'production'])
@pytest.mark.parametrize('password', ['Demo12345!', 'Admin123!', 'learner_ro_dev'])
@pytest.mark.parametrize('field', ['jwt_secret', 'smtp_password', 'google_client_secret', 'github_client_secret', 'llm_api_key'])
def test_known_demo_configuration_is_refused(mode, password, field):
    with pytest.raises(ValidationError, match='Unsafe ' + field.upper()):
        deployment_settings(mode, **{field: password})


@pytest.mark.parametrize('field', ['database_url', 'sandbox_url', 'sandbox_admin_url'])
def test_known_demo_database_password_is_refused(field):
    with pytest.raises(ValidationError, match='Unsafe ' + field.upper()):
        deployment_settings(**{field: 'postgresql://account:Demo12345!@distinct-host/dbcas'})


def test_development_configuration_accepts_public_demo_values():
    settings = Settings(_env_file=None, deployment_mode='development', jwt_secret='Demo12345!',
                        smtp_password='Demo12345!', google_client_secret='Demo12345!')
    assert settings.deployment_mode == 'development'
