"""RBAC tests — UC04 provisioning and role-gated endpoints."""

from app.security import hash_password


def _register(client, email="learner@test.dev"):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Le",
            "email": email,
            "password": "Secret123!",
            "password_confirm": "Secret123!",
        },
    )
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Secret123!"},
    ).json()["access_token"]


def _admin_token(client, db_session):
    """Provision an admin through the API path, activate it, log in."""
    from app.models import Account, AccountRole, Role, UserProfile

    role = db_session.query(Role).filter_by(role_name="Administrator").one()
    account = Account(
        email="root@test.dev",
        password_hash=hash_password("Admin123!"),
        status="active",
        can_manage_roles=True,
    )
    account.profile = UserProfile(full_name="Root")
    db_session.add(account)
    db_session.flush()
    db_session.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db_session.commit()
    return client.post(
        "/api/v1/auth/login",
        json={"email": "root@test.dev", "password": "Admin123!"},
    ).json()["access_token"]


def test_admin_endpoint_unauthenticated(client):
    r = client.post(
        "/api/v1/admin/accounts",
        json={"name": "X", "email": "x@x.dev", "password": "Secret123!"},
    )
    assert r.status_code == 401


def test_admin_endpoint_forbidden_for_learner(client, db_session):
    token = _register(client)
    r = client.post(
        "/api/v1/admin/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "X", "email": "x@x.dev", "password": "Secret123!"},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "forbidden"


def test_admin_can_provision_disabled_admin(client, db_session):
    token = _admin_token(client, db_session)
    r = client.post(
        "/api/v1/admin/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Admin", "email": "new@test.dev", "password": "Secret123!"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["roles"] == ["Administrator"]
    assert body["status"] == "disabled"


def test_ordinary_administrator_cannot_provision_administrator(client, db_session):
    from app.models import Account, AccountRole, Role, UserProfile
    role = db_session.query(Role).filter_by(role_name="Administrator").one()
    account = Account(email="ordinary@test.dev", password_hash=hash_password("Admin123!"), status="active")
    account.profile = UserProfile(full_name="Ordinary admin")
    db_session.add(account)
    db_session.flush()
    db_session.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db_session.commit()
    token = client.post("/api/v1/auth/login", json={"email": account.email, "password": "Admin123!"}).json()["access_token"]
    response = client.post("/api/v1/admin/accounts", headers={"Authorization": f"Bearer {token}"},
        json={"name": "Escalated", "email": "escalated@test.dev", "password": "Secret123!"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "role_management_forbidden"


def test_disabled_admin_cannot_login(client, db_session):
    token = _admin_token(client, db_session)
    client.post(
        "/api/v1/admin/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Admin", "email": "new@test.dev", "password": "Secret123!"},
    )
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "new@test.dev", "password": "Secret123!"},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "account_disabled"


def test_self_registration_never_grants_admin(client):
    """No way through the public register endpoint to get the Admin role."""
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Le",
            "email": "l@t.dev",
            "password": "Secret123!",
            "password_confirm": "Secret123!",
            "role": "Administrator",
        },
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": "l@t.dev", "password": "Secret123!"}
    ).json()["access_token"]
    r = client.post(
        "/api/v1/admin/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "X", "email": "x@x.dev", "password": "Secret123!"},
    )
    assert r.status_code == 403
