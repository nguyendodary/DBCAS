import pytest
from app.bootstrap_admin import bootstrap
from app.errors import AppError
from app.models import Account
from app.schemas import ProvisionAccountRequest
from app.security import verify_password


def payload(**changes):
    return ProvisionAccountRequest(name='Initial administrator', email='bootstrap@test.dev', password='Private123!', **changes)


def test_bootstrap_creates_first_admin_with_hash_and_active_role(db_session):
    account = db_session.get(Account, bootstrap(db_session, payload()))
    assert account.status == 'active'
    assert [r.role_name for r in account.roles] == ['Administrator']
    assert account.can_manage_roles is True
    from app.models import AccountRoleAudit
    audit = db_session.query(AccountRoleAudit).one()
    assert audit.action_type == 'ROLE_MANAGER_BOOTSTRAPPED'
    assert audit.actor_account_id is None and audit.target_account_id == account.account_id
    assert account.password_hash != 'Private123!'
    assert verify_password('Private123!', account.password_hash)


def test_bootstrap_never_replaces_an_existing_administrator(db_session):
    bootstrap(db_session, payload())
    with pytest.raises(AppError) as error:
        bootstrap(db_session, payload())
    assert error.value.code == 'administrator_exists'
    assert db_session.query(Account).count() == 1


def test_bootstrap_rejects_public_development_password(db_session):
    request = ProvisionAccountRequest(name='Initial administrator', email='bootstrap@test.dev', password='Admin123!')
    with pytest.raises(AppError) as error:
        bootstrap(db_session, request)
    assert error.value.code == 'unsafe_password'
    assert db_session.query(Account).count() == 0
