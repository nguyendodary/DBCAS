"""Session lifecycle endpoint tests — UC18 list first; serve/finish flows
join in the adaptive engine work."""

from datetime import datetime, timedelta, timezone

import pytest

from app.models import (
    Account,
    AccountRole,
    Assessment,
    AssessmentSession,
    Attempt,
    Question,
    Role,
    UserProfile,
)
from app.security import hash_password

LIST_URL = "/api/v1/sessions"


def _login(client, email, password="Secret123!"):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]


def _make_learner(db, email="learner@test.dev", name="Learner One"):
    account = Account(
        email=email, password_hash=hash_password("Secret123!"), status="active"
    )
    account.profile = UserProfile(full_name=name)
    role = db.query(Role).filter_by(role_name="Learner").one()
    db.add(account)
    db.flush()
    db.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db.commit()
    return account


def _make_admin(db, email="admin@test.dev"):
    account = Account(
        email=email, password_hash=hash_password("Secret123!"), status="active"
    )
    account.profile = UserProfile(full_name="Admin")
    role = db.query(Role).filter_by(role_name="Administrator").one()
    db.add(account)
    db.flush()
    db.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db.commit()
    return account


def _make_session(db, learner, *, title="Assessment", status="completed",
                  started_at=None, submitted_at=None):
    assessment = Assessment(
        title=title, status="published", created_by=learner.account_id
    )
    db.add(assessment)
    db.flush()
    now = datetime.now(timezone.utc)
    session = AssessmentSession(
        assessment_id=assessment.assessment_id,
        learner_id=learner.account_id,
        status=status,
        started_at=started_at or now - timedelta(hours=1),
        expires_at=(started_at or now) + timedelta(minutes=60),
        submitted_at=submitted_at,
    )
    db.add(session)
    db.flush()
    return session


def _serve(db, session, seq, *, submitted=True):
    q = Question(
        question_type="mcq",
        prompt="p",
        status="validated",
        created_by=session.learner_id,
    )
    db.add(q)
    db.flush()
    db.add(
        Attempt(
            session_id=session.session_id,
            question_id=q.question_id,
            seq_no=seq,
            submitted_at=datetime.now(timezone.utc) if submitted else None,
        )
    )
    db.flush()


@pytest.fixture()
def learner_a(client, db_session):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Learner A",
            "email": "a@test.dev",
            "password": "Secret123!",
            "password_confirm": "Secret123!",
        },
    )
    return {"token": _login(client, "a@test.dev")}


class TestSessionList:
    def test_unauthenticated_401(self, client):
        assert client.get(LIST_URL).status_code == 401

    def test_admin_forbidden(self, client, db_session):
        _make_admin(db_session)
        token = _login(client, "admin@test.dev")
        r = client.get(LIST_URL, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_lists_own_sessions_newest_first(self, client, db_session, learner_a):
        learner = db_session.query(Account).filter_by(email="a@test.dev").one()
        now = datetime.now(timezone.utc)
        older = _make_session(
            db_session, learner, title="Old",
            started_at=now - timedelta(days=2),
            submitted_at=now - timedelta(days=2),
        )
        newer = _make_session(
            db_session, learner, title="New", status="in_progress",
            started_at=now - timedelta(hours=1),
        )
        _serve(db_session, newer, 1, submitted=True)
        _serve(db_session, newer, 2, submitted=False)
        db_session.commit()

        r = client.get(
            LIST_URL, headers={"Authorization": f"Bearer {learner_a['token']}"}
        )
        assert r.status_code == 200
        body = r.json()
        assert [s["session_id"] for s in body] == [
            newer.session_id,
            older.session_id,
        ]
        first = body[0]
        assert first["assessment_title"] == "New"
        assert first["status"] == "in_progress"
        assert first["served_count"] == 2
        assert first["answered_count"] == 1

    def test_never_lists_other_learners_sessions(self, client, db_session):
        owner = _make_learner(db_session, email="owner@test.dev")
        _make_session(db_session, owner, title="Private")
        db_session.commit()

        client.post(
            "/api/v1/auth/register",
            json={
                "name": "B",
                "email": "b@test.dev",
                "password": "Secret123!",
                "password_confirm": "Secret123!",
            },
        )
        token = _login(client, "b@test.dev")
        r = client.get(LIST_URL, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json() == []
