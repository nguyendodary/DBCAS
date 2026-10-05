"""UC04 account lifecycle + UC05 curriculum management tests."""

from app.models import (
    Account,
    AccountRole,
    CloConcept,
    Concept,
    ConceptDependency,
    Question,
    QuestionConcept,
    Role,
    UserProfile,
)
from app.security import hash_password

BASE = "/api/v1/admin"


def _login(client, email, password="Secret123!"):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]


def _make_account(db, email, role_name, status="active", name=None):
    account = Account(
        email=email, password_hash=hash_password("Secret123!"), status=status
    )
    account.profile = UserProfile(full_name=name or email)
    role = db.query(Role).filter_by(role_name=role_name).one()
    db.add(account)
    db.flush()
    db.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db.commit()
    return account


def _admin_headers(client, db_session):
    _make_account(db_session, "admin@test.dev", "Administrator")
    return {"Authorization": f"Bearer {_login(client, 'admin@test.dev')}"}


def _concept(db, code, **kw):
    c = Concept(
        concept_code=code,
        concept_name=kw.get("name", code),
        subject_area=kw.get("area", "SQL Querying"),
        difficulty_level=kw.get("level", 2),
    )
    db.add(c)
    db.flush()
    return c


class TestAccountLifecycle:
    """UC04 — provision → disabled → manual verify → activate."""

    def test_provisioned_admin_cannot_login_until_activated(
        self, client, db_session
    ):
        h = _admin_headers(client, db_session)
        r = client.post(
            f"{BASE}/accounts",
            json={
                "name": "New Admin",
                "email": "new-admin@test.dev",
                "password": "Secret123!",
                "role": "Administrator",
            },
            headers=h,
        )
        assert r.status_code == 201
        assert r.json()["status"] == "disabled"

        # disabled → login refused with 403
        bad = client.post(
            "/api/v1/auth/login",
            json={"email": "new-admin@test.dev", "password": "Secret123!"},
        )
        assert bad.status_code == 403

        # roster shows the disabled account
        roster = client.get(f"{BASE}/accounts", headers=h)
        assert roster.status_code == 200
        row = next(a for a in roster.json() if a["email"] == "new-admin@test.dev")
        assert row["status"] == "disabled"

        # activate → login works
        act = client.patch(
            f"{BASE}/accounts/{row['account_id']}",
            json={"status": "active"},
            headers=h,
        )
        assert act.status_code == 200
        assert act.json()["status"] == "active"
        ok = client.post(
            "/api/v1/auth/login",
            json={"email": "new-admin@test.dev", "password": "Secret123!"},
        )
        assert ok.status_code == 200
        assert "Administrator" in ok.json()["account"]["roles"]

    def test_status_patch_validation_and_404(self, client, db_session):
        h = _admin_headers(client, db_session)
        bad = client.patch(
            f"{BASE}/accounts/1", json={"status": "banned"}, headers=h
        )
        assert bad.status_code == 422
        missing = client.patch(
            f"{BASE}/accounts/999999", json={"status": "active"}, headers=h
        )
        assert missing.status_code == 404

    def test_admin_cannot_disable_self(self, client, db_session):
        h = _admin_headers(client, db_session)
        me = db_session.query(Account).filter_by(email="admin@test.dev").one()
        r = client.patch(
            f"{BASE}/accounts/{me.account_id}",
            json={"status": "disabled"},
            headers=h,
        )
        assert r.status_code == 409

    def test_learner_cannot_manage_accounts(self, client, db_session):
        _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "learner@test.dev", "Learner")
        h = {"Authorization": f"Bearer {_login(client, 'learner@test.dev')}"}
        assert client.get(f"{BASE}/accounts", headers=h).status_code == 403
        assert client.patch(
            f"{BASE}/accounts/1", json={"status": "active"}, headers=h
        ).status_code == 403


class TestConcepts:
    def test_crud_roundtrip(self, client, db_session):
        h = _admin_headers(client, db_session)
        r = client.post(
            f"{BASE}/concepts",
            json={
                "concept_code": "SQL-CTE",
                "concept_name": "Common Table Expressions",
                "subject_area": "SQL Querying",
                "description": "WITH clauses",
                "difficulty_level": 4,
            },
            headers=h,
        )
        assert r.status_code == 201
        cid = r.json()["concept_id"]

        dup = client.post(
            f"{BASE}/concepts",
            json={
                "concept_code": "SQL-CTE",
                "concept_name": "dup",
                "subject_area": "x",
            },
            headers=h,
        )
        assert dup.status_code == 409

        up = client.patch(
            f"{BASE}/concepts/{cid}",
            json={"difficulty_level": 3, "description": "updated"},
            headers=h,
        )
        assert up.status_code == 200
        assert up.json()["difficulty_level"] == 3
        assert up.json()["description"] == "updated"

        listed = client.get(f"{BASE}/concepts", headers=h).json()
        assert any(c["concept_code"] == "SQL-CTE" for c in listed)

        assert client.delete(f"{BASE}/concepts/{cid}", headers=h).status_code == 204
        assert client.get(f"{BASE}/concepts/{cid}", headers=h).status_code in (
            404, 405
        ) or not any(
            c["concept_id"] == cid
            for c in client.get(f"{BASE}/concepts", headers=h).json()
        )

    def test_validation_bounds(self, client, db_session):
        h = _admin_headers(client, db_session)
        r = client.post(
            f"{BASE}/concepts",
            json={
                "concept_code": "X",
                "concept_name": "x",
                "subject_area": "x",
                "difficulty_level": 6,
            },
            headers=h,
        )
        assert r.status_code == 422

    def test_delete_blocked_when_referenced(self, client, db_session):
        h = _admin_headers(client, db_session)
        c = _concept(db_session, "SQL-REF")
        q = Question(
            question_type="mcq", prompt="p", status="validated",
            created_by=db_session.query(Account).first().account_id,
        )
        db_session.add(q)
        db_session.flush()
        db_session.add(
            QuestionConcept(
                question_id=q.question_id, concept_id=c.concept_id, confirmed=True
            )
        )
        db_session.commit()

        r = client.delete(f"{BASE}/concepts/{c.concept_id}", headers=h)
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "concept_in_use"

        # remove the reference, delete succeeds
        db_session.query(QuestionConcept).filter_by(
            concept_id=c.concept_id
        ).delete()
        db_session.commit()
        assert client.delete(f"{BASE}/concepts/{c.concept_id}", headers=h).status_code == 204

    def test_delete_blocked_by_dependency_edge(self, client, db_session):
        h = _admin_headers(client, db_session)
        a = _concept(db_session, "C-A")
        b = _concept(db_session, "C-B")
        db_session.add(
            ConceptDependency(
                concept_id=a.concept_id,
                prerequisite_concept_id=b.concept_id,
            )
        )
        db_session.commit()
        r = client.delete(f"{BASE}/concepts/{b.concept_id}", headers=h)
        assert r.status_code == 409


class TestClos:
    def test_crud_and_mapping_flow(self, client, db_session):
        h = _admin_headers(client, db_session)
        c1 = _concept(db_session, "SQL-SELECT")
        c2 = _concept(db_session, "SQL-WHERE")
        db_session.commit()

        r = client.post(
            f"{BASE}/clos",
            json={"clo_code": "CLO1", "title": "Write SELECT queries"},
            headers=h,
        )
        assert r.status_code == 201
        clo_id = r.json()["clo_id"]

        dup = client.post(
            f"{BASE}/clos",
            json={"clo_code": "CLO1", "title": "dup"},
            headers=h,
        )
        assert dup.status_code == 409

        # admin-confirmed mapping set
        m = client.put(
            f"{BASE}/clos/{clo_id}/concepts",
            json={"concept_ids": [c1.concept_id, c2.concept_id]},
            headers=h,
        )
        assert m.status_code == 200
        links = {l["concept_id"]: l for l in m.json()["concepts"]}
        assert set(links) == {c1.concept_id, c2.concept_id}
        assert all(l["status"] == "confirmed" for l in links.values())
        assert all(l["mapping_source"] == "admin" for l in links.values())

        # replace removes the unlisted admin link
        m2 = client.put(
            f"{BASE}/clos/{clo_id}/concepts",
            json={"concept_ids": [c2.concept_id]},
            headers=h,
        )
        assert [l["concept_id"] for l in m2.json()["concepts"]] == [c2.concept_id]

        # delete blocked while mapped, allowed after unmapping
        assert client.delete(f"{BASE}/clos/{clo_id}", headers=h).status_code == 409
        client.put(f"{BASE}/clos/{clo_id}/concepts", json={"concept_ids": []}, headers=h)
        assert client.delete(f"{BASE}/clos/{clo_id}", headers=h).status_code == 204

    def test_mapping_unknowns_and_duplicates(self, client, db_session):
        h = _admin_headers(client, db_session)
        c1 = _concept(db_session, "SQL-SELECT")
        r = client.post(
            f"{BASE}/clos", json={"clo_code": "CLO1", "title": "t"}, headers=h
        )
        clo_id = r.json()["clo_id"]
        db_session.commit()

        assert client.put(
            f"{BASE}/clos/{clo_id}/concepts",
            json={"concept_ids": [c1.concept_id, c1.concept_id]},
            headers=h,
        ).status_code == 422
        missing = client.put(
            f"{BASE}/clos/{clo_id}/concepts",
            json={"concept_ids": [c1.concept_id, 999999]},
            headers=h,
        )
        assert missing.status_code == 404
        assert client.put(
            f"{BASE}/clos/999999/concepts", json={"concept_ids": []}, headers=h
        ).status_code == 404

    def test_ai_pending_links_survive_admin_replace(self, client, db_session):
        """UC06 review items are never silently deleted by the admin set."""
        h = _admin_headers(client, db_session)
        c1 = _concept(db_session, "SQL-SELECT")
        c2 = _concept(db_session, "AI-SUGGESTED")
        r = client.post(
            f"{BASE}/clos", json={"clo_code": "CLO1", "title": "t"}, headers=h
        )
        clo_id = r.json()["clo_id"]
        db_session.add(
            CloConcept(
                clo_id=clo_id, concept_id=c2.concept_id,
                mapping_source="ai", status="pending",
            )
        )
        db_session.commit()

        m = client.put(
            f"{BASE}/clos/{clo_id}/concepts",
            json={"concept_ids": [c1.concept_id]},
            headers=h,
        )
        links = {l["concept_id"]: l for l in m.json()["concepts"]}
        assert links[c2.concept_id]["status"] == "pending"
        assert links[c2.concept_id]["mapping_source"] == "ai"

    def test_patch_and_list(self, client, db_session):
        h = _admin_headers(client, db_session)
        r = client.post(
            f"{BASE}/clos", json={"clo_code": "CLO1", "title": "t"}, headers=h
        )
        clo_id = r.json()["clo_id"]
        up = client.patch(
            f"{BASE}/clos/{clo_id}", json={"status": "archived"}, headers=h
        )
        assert up.status_code == 200
        assert up.json()["status"] == "archived"
        listed = client.get(f"{BASE}/clos", headers=h).json()
        assert listed[0]["clo_code"] == "CLO1"
        assert client.patch(
            f"{BASE}/clos/999999", json={"title": "x"}, headers=h
        ).status_code == 404
