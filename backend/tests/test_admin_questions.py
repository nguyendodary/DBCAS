"""UC07 — question bank management endpoint tests."""

from app.models import (
    Account,
    AccountRole,
    Attempt,
    Concept,
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


def _mcq_payload(concept_id):
    return {
        "question_type": "mcq",
        "prompt": "Which clause filters rows?",
        "reference_answer": "WHERE",
        "difficulty_level": 1,
        "points": "1.0",
        "concept_ids": [concept_id],
        "options": [
            {"option_label": "A", "option_text": "WHERE", "is_correct": True},
            {"option_label": "B", "option_text": "ORDER BY", "is_correct": False},
        ],
    }


def _sql_payload(concept_id):
    return {
        "question_type": "sql",
        "prompt": "List all students",
        "reference_answer": "SELECT * FROM students",
        "difficulty_level": 2,
        "points": "4.0",
        "concept_ids": [concept_id],
        "required_concept_ids": [concept_id],
        "datasets": [
            {
                "dataset_name": "base",
                "setup_sql": "CREATE TABLE students(id int); INSERT INTO students VALUES (1)",
                "expected_result": {"columns": ["id"], "rows": [[1]]},
            }
        ],
    }


def _essay_payload(concept_id):
    return {
        "question_type": "essay",
        "prompt": "Explain normalization",
        "reference_answer": "...",
        "difficulty_level": 3,
        "points": "5.0",
        "concept_ids": [concept_id],
        "rubrics": [
            {
                "level_name": "Complete",
                "min_score": "4.0",
                "max_score": "5.0",
                "criteria": "Full explanation",
            },
            {
                "level_name": "Incomplete",
                "min_score": "0",
                "max_score": "1.0",
                "criteria": "Missing or wrong",
            },
        ],
    }


class TestRbac:
    def test_learner_and_anon_blocked(self, client, db_session):
        _make_account(db_session, "learner@test.dev", "Learner")
        h = {"Authorization": f"Bearer {_login(client, 'learner@test.dev')}"}
        assert client.get(f"{BASE}/questions").status_code == 401
        assert client.get(f"{BASE}/questions", headers=h).status_code == 403


class TestCreateAndRead:
    def test_create_mcq_roundtrip(self, client, db_session):
        h = _admin(client, db_session)
        c = _concept(db_session, "SQL-WHERE")
        db_session.commit()

        r = client.post(
            f"{BASE}/questions", json=_mcq_payload(c.concept_id), headers=h
        )
        assert r.status_code == 201, r.json()
        body = r.json()
        assert body["status"] == "draft"
        assert body["source"] == "bank"
        assert len(body["options"]) == 2
        assert body["concepts"][0]["confirmed"] is True
        assert body["concepts"][0]["tag_source"] == "admin"

        got = client.get(
            f"{BASE}/questions/{body['question_id']}", headers=h
        )
        assert got.status_code == 200
        assert got.json()["prompt"] == "Which clause filters rows?"
        assert client.get(f"{BASE}/questions/999999", headers=h).status_code == 404

    def test_create_sql_and_essay(self, client, db_session):
        h = _admin(client, db_session)
        c = _concept(db_session, "SQL-SELECT")
        db_session.commit()
        r1 = client.post(
            f"{BASE}/questions", json=_sql_payload(c.concept_id), headers=h
        )
        assert r1.status_code == 201, r1.json()
        assert len(r1.json()["datasets"]) == 1
        assert r1.json()["concepts"][0]["is_required"] is True

        r2 = client.post(
            f"{BASE}/questions", json=_essay_payload(c.concept_id), headers=h
        )
        assert r2.status_code == 201, r2.json()
        assert len(r2.json()["rubrics"]) == 2

    def test_type_mismatch_rejected(self, client, db_session):
        h = _admin(client, db_session)
        c = _concept(db_session, "C1")
        db_session.commit()
        p = _mcq_payload(c.concept_id)
        p["datasets"] = _sql_payload(c.concept_id)["datasets"]
        r = client.post(f"{BASE}/questions", json=p, headers=h)
        assert r.status_code == 422

    def test_unknown_concept_404_and_required_subset(self, client, db_session):
        h = _admin(client, db_session)
        c = _concept(db_session, "C1")
        db_session.commit()
        p = _mcq_payload(c.concept_id)
        p["concept_ids"].append(999999)
        assert client.post(f"{BASE}/questions", json=p, headers=h).status_code == 404

        p2 = _mcq_payload(c.concept_id)
        p2["required_concept_ids"] = [999999]
        assert client.post(f"{BASE}/questions", json=p2, headers=h).status_code == 422


class TestSearch:
    def test_filters(self, client, db_session):
        h = _admin(client, db_session)
        c1 = _concept(db_session, "SQL-WHERE")
        c2 = _concept(db_session, "DB-NORM")
        db_session.commit()
        client.post(f"{BASE}/questions", json=_mcq_payload(c1.concept_id), headers=h)
        p = _essay_payload(c2.concept_id)
        p["difficulty_level"] = 5
        client.post(f"{BASE}/questions", json=p, headers=h)

        all_q = client.get(f"{BASE}/questions", headers=h).json()
        assert len(all_q) == 2
        by_type = client.get(
            f"{BASE}/questions?question_type=essay", headers=h
        ).json()
        assert [i["question_type"] for i in by_type] == ["essay"]
        by_concept = client.get(
            f"{BASE}/questions?concept_id={c2.concept_id}", headers=h
        ).json()
        assert [i["question_type"] for i in by_concept] == ["essay"]
        by_diff = client.get(f"{BASE}/questions?difficulty=5", headers=h).json()
        assert len(by_diff) == 1
        by_q = client.get(f"{BASE}/questions?q=normalization", headers=h).json()
        assert len(by_q) == 1
        assert (
            client.get(f"{BASE}/questions?question_type=bad", headers=h).status_code
            == 422
        )


class TestStatusFlow:
    def test_validate_requires_complete_item(self, client, db_session):
        h = _admin(client, db_session)
        c = _concept(db_session, "C1")
        db_session.commit()

        # untagged → cannot validate
        p = _mcq_payload(c.concept_id)
        p["concept_ids"] = []
        r = client.post(f"{BASE}/questions", json=p, headers=h)
        qid = r.json()["question_id"]
        bad = client.patch(
            f"{BASE}/questions/{qid}", json={"status": "validated"}, headers=h
        )
        assert bad.status_code == 422
        assert bad.json()["error"]["code"] == "question_incomplete"

        # complete → validates
        r2 = client.post(
            f"{BASE}/questions", json=_mcq_payload(c.concept_id), headers=h
        )
        ok = client.patch(
            f"{BASE}/questions/{r2.json()['question_id']}",
            json={"status": "validated"},
            headers=h,
        )
        assert ok.status_code == 200
        assert ok.json()["status"] == "validated"

    def test_edit_demotes_validated_to_draft(self, client, db_session):
        h = _admin(client, db_session)
        c = _concept(db_session, "C1")
        db_session.commit()
        r = client.post(
            f"{BASE}/questions", json=_mcq_payload(c.concept_id), headers=h
        )
        qid = r.json()["question_id"]
        client.patch(f"{BASE}/questions/{qid}", json={"status": "validated"}, headers=h)

        edited = _mcq_payload(c.concept_id)
        edited["prompt"] = "Changed prompt"
        up = client.put(f"{BASE}/questions/{qid}", json=edited, headers=h)
        assert up.status_code == 200
        assert up.json()["status"] == "draft"
        assert up.json()["prompt"] == "Changed prompt"


class TestDelete:
    def test_delete_unreferenced(self, client, db_session):
        h = _admin(client, db_session)
        c = _concept(db_session, "C1")
        db_session.commit()
        r = client.post(
            f"{BASE}/questions", json=_mcq_payload(c.concept_id), headers=h
        )
        qid = r.json()["question_id"]
        assert client.delete(f"{BASE}/questions/{qid}", headers=h).status_code == 204
        assert client.get(f"{BASE}/questions/{qid}", headers=h).status_code == 404

    def test_delete_blocked_by_attempt(self, client, db_session):
        from datetime import datetime, timezone

        from app.models import AssessmentSession
        h = _admin(client, db_session)
        c = _concept(db_session, "C1")
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
        learner = _make_account(db_session, "l@test.dev", "Learner")
        from app.models import Assessment
        a = Assessment(title="t", status="published", created_by=learner.account_id)
        db_session.add(a)
        db_session.flush()
        s = AssessmentSession(
            assessment_id=a.assessment_id, learner_id=learner.account_id,
            status="completed", expires_at=datetime.now(timezone.utc),
            submitted_at=datetime.now(timezone.utc),
        )
        db_session.add(s)
        db_session.flush()
        db_session.add(
            Attempt(
                session_id=s.session_id, question_id=q.question_id, seq_no=1,
                submitted_at=datetime.now(timezone.utc),
            )
        )
        db_session.commit()

        r = client.delete(f"{BASE}/questions/{q.question_id}", headers=h)
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "question_in_use"
