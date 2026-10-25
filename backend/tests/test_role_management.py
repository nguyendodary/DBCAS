"""Security and lifecycle tests for explicitly authorized role management."""
import pytest
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor

from app.errors import AppError
from app.models import Account, AccountRole, AccountRoleAudit, Role, UserProfile
from app.security import hash_password


PASSWORD = "Private-Role-123!"


def _account(db, email, role_name, *, manager=False, status="active"):
    account = Account(email=email, password_hash=hash_password(PASSWORD), status=status,
                      can_manage_roles=manager)
    account.profile = UserProfile(full_name=email.split("@")[0])
    db.add(account)
    db.flush()
    role = db.query(Role).filter_by(role_name=role_name).one()
    db.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db.commit()
    return account


def _token(client, email):
    result = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert result.status_code == 200
    return result.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_role_manager_promotes_learner_and_audits_once(client, db_session):
    manager = _account(db_session, "manager@roles.test", "Administrator", manager=True)
    learner = _account(db_session, "learner@roles.test", "Learner")
    token = _token(client, manager.email)

    response = client.patch(f"/api/v1/admin/accounts/{learner.account_id}/role", headers=_headers(token),
        json={"role": "Administrator", "expected_role": "Learner"})
    assert response.status_code == 200
    assert response.json()["changed"] is True
    assert response.json()["account"]["roles"] == ["Administrator"]
    db_session.expire_all()
    promoted = db_session.get(Account, learner.account_id)
    assert promoted.can_manage_roles is False
    audit = db_session.query(AccountRoleAudit).one()
    assert (audit.actor_account_id, audit.target_account_id, audit.previous_role, audit.new_role) == (
        manager.account_id, learner.account_id, "Learner", "Administrator")
    assert audit.action_type == "ROLE_GRANTED"

    no_op = client.patch(f"/api/v1/admin/accounts/{learner.account_id}/role", headers=_headers(token),
        json={"role": "Administrator", "expected_role": "Administrator"})
    assert no_op.status_code == 200 and no_op.json()["changed"] is False
    assert db_session.query(AccountRoleAudit).count() == 1


def test_demoted_users_lose_access_with_existing_access_and_renewal_tokens(client, db_session):
    manager = _account(db_session, "manager2@roles.test", "Administrator", manager=True)
    target = _account(db_session, "target@roles.test", "Administrator")
    manager_token = _token(client, manager.email)
    stale_admin_token = _token(client, target.email)

    changed = client.patch(f"/api/v1/admin/accounts/{target.account_id}/role", headers=_headers(manager_token),
        json={"role": "Learner", "expected_role": "Administrator"})
    assert changed.status_code == 200
    assert changed.json()["account"]["roles"] == ["Learner"]
    assert client.get("/api/v1/admin/accounts", headers=_headers(stale_admin_token)).status_code == 403
    assert client.get("/api/v1/auth/me", headers=_headers(stale_admin_token)).json()["roles"] == ["Learner"]
    renewed = client.post("/api/v1/auth/renew", headers=_headers(stale_admin_token))
    assert renewed.status_code == 200
    assert renewed.json()["account"]["roles"] == ["Learner"]
    audit = db_session.query(AccountRoleAudit).filter_by(action_type="ROLE_REVOKED").one()
    assert audit.actor_account_id == manager.account_id and audit.target_account_id == target.account_id


def test_learner_and_ordinary_administrator_cannot_change_roles(client, db_session):
    learner = _account(db_session, "ordinary-learner@roles.test", "Learner")
    ordinary = _account(db_session, "ordinary-admin@roles.test", "Administrator")
    target = _account(db_session, "target2@roles.test", "Learner")
    payload = {"role": "Administrator", "expected_role": "Learner"}
    assert client.patch(f"/api/v1/admin/accounts/{target.account_id}/role", json=payload).status_code == 401
    for account in (learner, ordinary):
        result = client.patch(f"/api/v1/admin/accounts/{target.account_id}/role",
            headers=_headers(_token(client, account.email)), json=payload)
        assert result.status_code == 403
    assert db_session.query(AccountRoleAudit).count() == 0


def test_capability_and_role_audit_endpoints_are_restricted(client, db_session):
    manager = _account(db_session, "manager4@roles.test", "Administrator", manager=True)
    ordinary = _account(db_session, "ordinary4@roles.test", "Administrator")
    learner = _account(db_session, "learner4@roles.test", "Learner")
    manager_token = _token(client, manager.email)
    ordinary_token = _token(client, ordinary.email)
    assert client.get("/api/v1/admin/role-management/capability", headers=_headers(manager_token)).json() == {
        "account_id": manager.account_id, "can_manage_roles": True}
    assert client.get("/api/v1/admin/role-management/capability", headers=_headers(ordinary_token)).json() == {
        "account_id": ordinary.account_id, "can_manage_roles": False}
    changed = client.patch(f"/api/v1/admin/accounts/{learner.account_id}/role", headers=_headers(manager_token),
        json={"role": "Administrator", "expected_role": "Learner"})
    assert changed.status_code == 200
    assert len(client.get("/api/v1/admin/accounts/role-audit", headers=_headers(manager_token)).json()) == 1
    assert client.get("/api/v1/admin/accounts/role-audit", headers=_headers(ordinary_token)).status_code == 403


def test_only_role_manager_can_activate_an_administrator_account(client, db_session):
    manager = _account(db_session, "manager5@roles.test", "Administrator", manager=True)
    ordinary = _account(db_session, "ordinary5@roles.test", "Administrator")
    target = _account(db_session, "provisioned5@roles.test", "Administrator", status="disabled")
    ordinary_response = client.patch(f"/api/v1/admin/accounts/{target.account_id}",
        headers=_headers(_token(client, ordinary.email)), json={"status": "active"})
    assert ordinary_response.status_code == 403
    manager_response = client.patch(f"/api/v1/admin/accounts/{target.account_id}",
        headers=_headers(_token(client, manager.email)), json={"status": "active"})
    assert manager_response.status_code == 200
    assert manager_response.json()["status"] == "active"


def test_role_change_validates_target_role_expected_state_and_account_status(client, db_session):
    manager = _account(db_session, "manager3@roles.test", "Administrator", manager=True)
    learner = _account(db_session, "target3@roles.test", "Learner")
    disabled = _account(db_session, "disabled@roles.test", "Learner", status="disabled")
    token = _token(client, manager.email)

    invalid_role = client.patch(f"/api/v1/admin/accounts/{learner.account_id}/role", headers=_headers(token),
        json={"role": "Owner", "expected_role": "Learner"})
    assert invalid_role.status_code == 422
    missing = client.patch("/api/v1/admin/accounts/99999/role", headers=_headers(token),
        json={"role": "Administrator", "expected_role": "Learner"})
    assert missing.status_code == 404
    stale = client.patch(f"/api/v1/admin/accounts/{learner.account_id}/role", headers=_headers(token),
        json={"role": "Administrator", "expected_role": "Administrator"})
    assert stale.status_code == 409
    inactive = client.patch(f"/api/v1/admin/accounts/{disabled.account_id}/role", headers=_headers(token),
        json={"role": "Administrator", "expected_role": "Learner"})
    assert inactive.status_code == 409
    assert db_session.query(AccountRoleAudit).count() == 0


def test_concurrent_stale_role_changes_serialize_without_lost_audit(client, db_session):
    managers = [
        _account(db_session, "concurrent-a@roles.test", "Administrator", manager=True),
        _account(db_session, "concurrent-b@roles.test", "Administrator", manager=True),
    ]
    target = _account(db_session, "concurrent-target@roles.test", "Learner")
    tokens = [_token(client, manager.email) for manager in managers]
    def change(token):
        return client.patch(f"/api/v1/admin/accounts/{target.account_id}/role", headers=_headers(token),
            json={"role": "Administrator", "expected_role": "Learner"}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(change, tokens))
    assert sorted(results) == [200, 409]
    assert db_session.query(AccountRoleAudit).count() == 1


def test_self_demotion_is_rejected_and_stale_role_manager_status_does_not_authorize(client, db_session):
    manager = _account(db_session, "self@roles.test", "Administrator", manager=True)
    token = _token(client, manager.email)
    response = client.patch(f"/api/v1/admin/accounts/{manager.account_id}/role", headers=_headers(token),
        json={"role": "Learner", "expected_role": "Administrator"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "cannot_demote_self"
    assert db_session.query(AccountRoleAudit).count() == 0


@pytest.mark.parametrize("guard,error_code", [
    ("active_administrator_count", "last_administrator"),
    ("active_role_manager_count", "last_role_manager"),
])
def test_final_admin_and_role_manager_guards_are_enforced(client, db_session, monkeypatch, guard, error_code):
    manager = _account(db_session, f"manager-{guard}@roles.test", "Administrator", manager=True)
    target = _account(db_session, f"target-{guard}@roles.test", "Administrator", manager=(guard == "active_role_manager_count"))
    from app.repositories import AccountRepository
    monkeypatch.setattr(AccountRepository, guard, lambda _repo: 1)
    response = client.patch(f"/api/v1/admin/accounts/{target.account_id}/role", headers=_headers(_token(client, manager.email)),
        json={"role": "Learner", "expected_role": "Administrator"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == error_code
    db_session.expire_all()
    assert [role.role_name for role in db_session.get(Account, target.account_id).roles] == ["Administrator"]


def test_registration_ignores_supplied_role_and_keeps_learner_role(client):
    response = client.post("/api/v1/auth/register", json={"name": "New", "email": "new-role@test.dev",
        "password": PASSWORD, "password_confirm": PASSWORD, "role": "Administrator",
        "can_manage_roles": True})
    assert response.status_code == 201
    assert response.json()["roles"] == ["Learner"]
    assert client.post("/api/v1/auth/login", json={"email": "new-role@test.dev", "password": PASSWORD}).json()["account"]["roles"] == ["Learner"]


def test_role_audit_is_database_immutable(db_session):
    manager = _account(db_session, "audit-manager@roles.test", "Administrator", manager=True)
    learner = _account(db_session, "audit-target@roles.test", "Learner")
    from app.repositories import AccountRepository
    repo = AccountRepository(db_session)
    repo.add_role_audit(action_type="ROLE_GRANTED", actor_account_id=manager.account_id,
        target_account_id=learner.account_id, previous_role="Learner", new_role="Administrator")
    db_session.commit()
    event_id = db_session.scalar(text("SELECT audit_id FROM account_role_audit LIMIT 1"))
    with pytest.raises(Exception):
        with db_session.begin_nested():
            db_session.execute(text("UPDATE account_role_audit SET new_role='Learner' WHERE audit_id=:id"), {"id": event_id})
    with pytest.raises(Exception):
        with db_session.begin_nested():
            db_session.execute(text("DELETE FROM account_role_audit WHERE audit_id=:id"), {"id": event_id})


def test_explicit_bootstrap_assigns_only_selected_active_administrator(db_session):
    from app.bootstrap_role_manager import bootstrap_role_manager
    admin = _account(db_session, "bootstrap-target@roles.test", "Administrator")
    with pytest.raises(AppError) as mismatch:
        bootstrap_role_manager(db_session, admin.account_id, "wrong@roles.test")
    assert mismatch.value.code == "account_confirmation_mismatch"
    assert db_session.get(Account, admin.account_id).can_manage_roles is False
    assert bootstrap_role_manager(db_session, admin.account_id, admin.email) == admin.account_id
    db_session.expire_all()
    assert db_session.get(Account, admin.account_id).can_manage_roles is True
    assert db_session.query(AccountRoleAudit).filter_by(action_type="ROLE_MANAGER_BOOTSTRAPPED").count() == 1
    with pytest.raises(AppError) as duplicate:
        bootstrap_role_manager(db_session, admin.account_id, admin.email)
    assert duplicate.value.code == "role_manager_exists"
