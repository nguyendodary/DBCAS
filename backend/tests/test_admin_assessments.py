"""UC09 — adaptive assessment configuration tests (+ learner list)."""

from app.models import (
    Account,
    AccountRole,
    AssessmentSession,
    Concept,
    Role,
    UserProfile,
)
from app.security import hash_password
from datetime import datetime, timezone

BASE = "/api/v1/admin"


def _login(client, email, password="Secret123!"):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]


def _make_account(db, email, role_name):
    account = Account(
        email=email, password_hash=hash_password("Secret123!"), status="active"
    )
    account.profile = UserProfile(full_name=email)
    role = db.query(Role).filter_by(role_name=role_name).one()
    db.add(account)
    db.flush()
    db.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db.commit()
    return account


def _concept(db, code):
    c = Concept(
        concept_code=code, concept_name=code, subject_area="SQL Querying",
        difficulty_level=2,
    )
    db.add(c)
    db.flush()
    return c


def _admin(client, db_session):
    _make_account(db_session, "admin@test.dev", "Administrator")
    return {"Authorization": f"Bearer {_login(client, 'admin@test.dev')}"}


def _payload(*concept_ids):
    return {
        "title": "PostgreSQL Midterm",
        "description": "Adaptive check",
        "max_questions": 13,
        "duration_min": 60,
        "target_mcq": 10,
        "target_sql": 2,
        "target_essay": 1,
        "concepts": [
            {
                "concept_id": cid,
                "min_difficulty": 1,
                "max_difficulty": 3,
                "target_pct": "60.00",
            }
            for cid in concept_ids
        ],
    }


class TestRbac:
    def test_learner_and_anon_blocked(self, client, db_session):
        _make_account(db_session, "l@test.dev", "Learner")
        h = {"Authorization": f"Bearer {_login(client, 'l@test.dev')}"}
        assert client.get(f"{BASE}/assessments").status_code == 401
        assert client.get(f"{BASE}/assessments", headers=h).status_code == 403


class TestCreateAndValidation:
    def test_create_with_targets(self, client, db_session):
        h = _admin(client, db_session)
        c1, c2 = _concept(db_session, "C1"), _concept(db_session, "C2")
        db_session.commit()
        r = client.post(
            f"{BASE}/assessments", json=_payload(c1.concept_id, c2.concept_id),
            headers=h,
        )
        assert r.status_code == 201, r.json()
        body = r.json()
        assert body["status"] == "draft"
        assert len(body["concepts"]) == 2
        assert body["concepts"][0]["target_pct"] == "60.00"
        assert body["concepts"][0]["min_difficulty"] == 1
        assert body["concepts"][0]["max_difficulty"] == 3

    def test_no_target_concept_422(self, client, db_session):
        h = _admin(client, db_session)
        p = _payload()
        p["concepts"] = []
        r = client.post(f"{BASE}/assessments", json=p, headers=h)
        assert r.status_code == 422

    def test_max_questions_bound_and_mix_sum(self, client, db_session):
        h = _admin(client, db_session)
        c = _concept(db_session, "C1")
        db_session.commit()
        p = _payload(c.concept_id)
        p["max_questions"] = 14
        assert client.post(f"{BASE}/assessments", json=p, headers=h).status_code == 422

        p2 = _payload(c.concept_id)
        p2["target_mcq"], p2["target_sql"], p2["target_essay"] = 12, 2, 1
        r2 = client.post(f"{BASE}/assessments", json=p2, headers=h)
        assert r2.status_code == 422
        assert r2.json()["error"]["code"] == "target_mix_too_large"

    def test_bad_difficulty_range_and_unknown_concept(self, client, db_session):
        h = _admin(client, db_session)
        c = _concept(db_session, "C1")
        db_session.commit()
        p = _payload(c.concept_id)
        p["concepts"][0]["min_difficulty"] = 4
        p["concepts"][0]["max_difficulty"] = 2
        assert client.post(f"{BASE}/assessments", json=p, headers=h).status_code == 422

        p2 = _payload(999999)
        r2 = client.post(f"{BASE}/assessments", json=p2, headers=h)
        assert r2.status_code == 404

        p3 = _payload(c.concept_id, c.concept_id)
        assert client.post(f"{BASE}/assessments", json=p3, headers=h).status_code == 422


class TestLifecycle:
    def test_draft_active_closed_flow(self, client, db_session):
        h = _admin(client, db_session)
        c = _concept(db_session, "C1")
        db_session.commit()
        r = client.post(f"{BASE}/assessments", json=_payload(c.concept_id), headers=h)
        aid = r.json()["assessment_id"]

        # draft → active
        ok = client.patch(
            f"{BASE}/assessments/{aid}", json={"status": "active"}, headers=h
        )
        assert ok.status_code == 200
        assert ok.json()["status"] == "active"

        # editing an active assessment → 409
        assert client.put(
            f"{BASE}/assessments/{aid}", json=_payload(c.concept_id), headers=h
        ).status_code == 409

        # invalid transition: active → draft is not allowed
        assert client.patch(
            f"{BASE}/assessments/{aid}", json={"status": "draft"}, headers=h
        ).status_code == 409

        # active → closed, closed → draft
        assert client.patch(
            f"{BASE}/assessments/{aid}", json={"status": "closed"}, headers=h
        ).status_code == 200
        assert client.patch(
            f"{BASE}/assessments/{aid}", json={"status": "draft"}, headers=h
        ).status_code == 200

    def test_edit_draft_replaces_targets(self, client, db_session):
        h = _admin(client, db_session)
        c1, c2 = _concept(db_session, "C1"), _concept(db_session, "C2")
        db_session.commit()
        r = client.post(f"{BASE}/assessments", json=_payload(c1.concept_id), headers=h)
        aid = r.json()["assessment_id"]

        up = client.put(
            f"{BASE}/assessments/{aid}", json=_payload(c2.concept_id), headers=h
        )
        assert up.status_code == 200
        assert [t["concept_id"] for t in up.json()["concepts"]] == [c2.concept_id]

    def test_delete_blocked_by_session(self, client, db_session):
        h = _admin(client, db_session)
        c = _concept(db_session, "C1")
        db_session.commit()
        r = client.post(f"{BASE}/assessments", json=_payload(c.concept_id), headers=h)
        aid = r.json()["assessment_id"]

        learner = _make_account(db_session, "l@test.dev", "Learner")
        db_session.add(
            AssessmentSession(
                assessment_id=aid,
                learner_id=learner.account_id,
                status="completed",
                expires_at=datetime.now(timezone.utc),
                submitted_at=datetime.now(timezone.utc),
            )
        )
        db_session.commit()
        assert client.delete(f"{BASE}/assessments/{aid}", headers=h).status_code == 409

        # a fresh unused assessment deletes fine
        r2 = client.post(
            f"{BASE}/assessments", json=_payload(c.concept_id), headers=h
        )
        assert (
            client.delete(
                f"{BASE}/assessments/{r2.json()['assessment_id']}", headers=h
            ).status_code
            == 204
        )


class TestLearnerList:
    def test_learners_see_only_active(self, client, db_session):
        _admin(client, db_session)
        h = {"Authorization": f"Bearer {_login(client, 'admin@test.dev')}"}
        c = _concept(db_session, "C1")
        db_session.commit()
        r = client.post(f"{BASE}/assessments", json=_payload(c.concept_id), headers=h)
        aid = r.json()["assessment_id"]
        client.post(
            f"{BASE}/assessments",
            json={**_payload(c.concept_id), "title": "Draft only"},
            headers=h,
        )
        client.patch(f"{BASE}/assessments/{aid}", json={"status": "active"}, headers=h)

        learner = _make_account(db_session, "l@test.dev", "Learner")
        lh = {"Authorization": f"Bearer {_login(client, 'l@test.dev')}"}
        r = client.get("/api/v1/assessments", headers=lh)
        assert r.status_code == 200
        titles = [a["title"] for a in r.json()]
        assert titles == ["PostgreSQL Midterm"]
        item = r.json()[0]
        assert item["concept_count"] == 1
        assert item["duration_min"] == 60

    def test_admin_cannot_use_learner_list(self, client, db_session):
        _admin(client, db_session)
        h = {"Authorization": f"Bearer {_login(client, 'admin@test.dev')}"}
        assert client.get("/api/v1/assessments", headers=h).status_code == 403
        assert client.get("/api/v1/assessments").status_code == 401
