"""Pure tests: no database connections or shared data mutations."""
import base64
from types import SimpleNamespace as Row
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.errors import AppError
from app.schemas import ChangePasswordRequest
from app.security import hash_password, verify_password, decode_access_token, create_access_token
from app.services import account_settings
from app import deps


@pytest.fixture
def setup_account(monkeypatch):
    account = Row(account_id=7, email='student@example.test', profile=None,
                  roles=[Row(role_name='Learner')], status='active',
                  password_hash=hash_password('old-password'), token_version=0,
                  avatar_data_url=None)
    db = Mock()
    repo = Row(get_for_update=lambda identifier: account if identifier == 7 else None,
               get_with_roles=lambda identifier: account if identifier == 7 else None)
    monkeypatch.setattr(account_settings, 'AccountRepository', lambda _: repo)
    monkeypatch.setattr(deps, 'AccountRepository', lambda _: repo)
    settings = Settings(_env_file=None, jwt_secret='test-secret-account-settings-at-least-32-characters')
    return account, db, settings


def payload(current='old-password'):
    return ChangePasswordRequest(current_password=current, new_password='new-password', new_password_confirm='new-password')


def test_password_changes_hash_and_revokes_previous_token(setup_account):
    account, db, settings = setup_account
    old_token, _ = create_access_token(7, ['Learner'], settings)
    result = account_settings.change_password(db, 7, payload(), settings)
    assert verify_password('new-password', account.password_hash)
    assert not verify_password('old-password', account.password_hash)
    assert decode_access_token(result.access_token, settings)['ver'] == 1
    assert deps.get_current_account('Bearer ' + result.access_token, db, settings) is account
    with pytest.raises(AppError) as error:
        deps.get_current_account('Bearer ' + old_token, db, settings)
    assert error.value.code == 'invalid_token'
    db.commit.assert_called_once()


def test_wrong_current_password_does_not_mutate(setup_account):
    account, db, settings = setup_account
    original = account.password_hash
    with pytest.raises(AppError) as error:
        account_settings.change_password(db, 7, payload('wrong-password'), settings)
    assert error.value.code == 'current_password_incorrect'
    assert account.password_hash == original and account.token_version == 0
    db.commit.assert_not_called()


@pytest.mark.parametrize('new,confirmation', [('short', 'short'), ('new-password', 'different'), ('é' * 40, 'é' * 40)])
def test_password_validation(new, confirmation):
    with pytest.raises(ValidationError):
        ChangePasswordRequest(current_password='old-password', new_password=new, new_password_confirm=confirmation)


PNG = 'data:image/png;base64,' + base64.b64encode(base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6WQAAAAASUVORK5CYII=')).decode()


def test_avatar_save_and_remove_are_persistent_and_scoped(setup_account):
    account, db, _ = setup_account
    assert account_settings.save_avatar(db, 7, PNG).avatar_url == PNG
    assert account.avatar_data_url == PNG
    assert account_settings.save_avatar(db, 7, None).avatar_url is None
    assert account.avatar_data_url is None
    assert db.commit.call_count == 2
    with pytest.raises(AppError):
        account_settings.save_avatar(db, 99, PNG)


@pytest.mark.parametrize('value', ['https://example.test/avatar.png', 'data:image/svg+xml;base64,PHN2Zz4=', 'data:image/png;base64,!!', 'data:image/png;base64,YWJj'])
def test_invalid_avatar_is_rejected(value):
    with pytest.raises(AppError) as error:
        account_settings.validate_avatar(value)
    assert error.value.code == 'invalid_avatar'
