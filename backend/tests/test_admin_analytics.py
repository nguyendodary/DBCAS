"""DBCAS-25 / UC20 — admin cohort analytics endpoints.

Covers RBAC (learner cannot reach cohort data), per-learner-latest
aggregation, gap prevalence ordering, the learner drill-down, and the
admin-scoped competency read.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models import (
    Account,
    AccountRole,
    Assessment,
    AssessmentConcept,
    AssessmentSession,
    Attempt,
    Concept,
    ConceptCompetency,
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


def _make_account(db, email, role_name, name=None):
    account = Account(
        email=email, password_hash=hash_password("Secret123!"), status="active"
    )
    account.profile = UserProfile(full_name=name or email)
    role = db.query(Role).filter_by(role_name=role_name).one()
    db.add(account)
    db.flush()
    db.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db.commit()
    return account


def _make_concept(db, code, name=None, area="SQL Querying"):
    c = Concept(
        concept_code=code,
        concept_name=name or code,
        subject_area=area,
        difficulty_level=2,
    )
    db.add(c)
    db.flush()
    return c


def _make_assessment(db, admin, targets):
    a = Assessment(title="A", status="published", created_by=admin.account_id)
    db.add(a)
    db.flush()
    for concept, target in targets.items():
        db.add(
            AssessmentConcept(
                assessment_id=a.assessment_id,
                concept_id=concept.concept_id,
                target_pct=Decimal(str(target)),
            )
        )
    db.flush()
    return a


def _session(db, learner, assessment, *, status="completed", days_ago=0):
    now = datetime.now(timezone.utc)
    s = AssessmentSession(
        assessment_id=assessment.assessment_id,
        learner_id=learner.account_id,
        status=status,
        started_at=now - timedelta(days=days_ago, hours=1),
        expires_at=now - timedelta(days=days_ago),
        submitted_at=(now - timedelta(days=days_ago)) if status != "in_progress" else None,
    )
    db.add(s)
    db.flush()
    return s


def _score(db, session, learner, concept, score, seq, points="4.0"):
    q = Question(
        question_type="mcq",
        prompt="p",
        points=Decimal(points),
        status="validated",
        created_by=learner.account_id,
    )
    db.add(q)
    db.flush()
    db.add(
        QuestionConcept(
            question_id=q.question_id, concept_id=concept.concept_id, confirmed=True
        )
    )
    db.add(
        Attempt(
            session_id=session.session_id,
            question_id=q.question_id,
            seq_no=seq,
            score=Decimal(str(score)),
            grading_detail={"grader": "answer_key"},
            submitted_at=datetime.now(timezone.utc),
        )
    )
    db.flush()


@pytest.fixture()
def admin(client, db_session):
    _make_account(db_session, "admin@test.dev", "Administrator", "Admin")
    return {"token": _login(client, "admin@test.dev")}


@pytest.fixture()
def learner(client, db_session):
    _make_account(db_session, "learner@test.dev", "Learner", "Learner")
    return {"token": _login(client, "learner@test.dev")}


def _seed_cohort(db):
    """Two learners, one assessment, two concepts with different standing."""
    admin = _make_account(db, "seed-admin@test.dev", "Administrator")
    l1 = _make_account(db, "l1@test.dev", "Learner", "One")
    l2 = _make_account(db, "l2@test.dev", "Learner", "Two")
    c_sel = _make_concept(db, "SQL-SELECT", "SELECT")
    c_join = _make_concept(db, "SQL-JOIN", "JOIN")
    a = _make_assessment(db, admin, {c_sel: "60.0", c_join: "60.0"})

    s1 = _session(db, l1, a)
    _score(db, s1, l1, c_sel, "4.0", 1)   # l1: SELECT 100%
    _score(db, s1, l1, c_join, "4.0", 2)  # l1: JOIN 100%

    s2 = _session(db, l2, a)
    _score(db, s2, l2, c_sel, "1.0", 1)   # l2: SELECT 25% (below)
    _score(db, s2, l2, c_join, "4.0", 2)  # l2: JOIN 100%

    db.commit()
    return admin, l1, l2, c_sel, c_join, a


class TestCohortRbac:
    def test_unauthenticated_401(self, client):
        for url in (
            f"{BASE}/analytics/cohort",
            f"{BASE}/learners",
            f"{BASE}/learners/1/sessions",
            f"{BASE}/sessions/1/competency",
        ):
            assert client.get(url).status_code == 401, url

    def test_learner_forbidden(self, client, learner):
        h = {"Authorization": f"Bearer {learner['token']}"}
        for url in (
            f"{BASE}/analytics/cohort",
            f"{BASE}/learners",
            f"{BASE}/learners/1/sessions",
            f"{BASE}/sessions/1/competency",
        ):
            assert client.get(url, headers=h).status_code == 403, url


class TestCohortOverview:
    def test_aggregates_and_orders_by_gap_rate(self, client, db_session, admin):
        _seed_cohort(db_session)
        r = client.get(
            f"{BASE}/analytics/cohort",
            headers={"Authorization": f"Bearer {admin['token']}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["learner_count"] == 2
        assert body["finalized_sessions"] == 2
        stats = {c["concept_code"]: c for c in body["concepts"]}
        sel, join = stats["SQL-SELECT"], stats["SQL-JOIN"]
        assert sel["learners_assessed"] == 2
        assert Decimal(sel["avg_competency_pct"]) == Decimal("62.50")
        assert sel["below_target_count"] == 1
        assert Decimal(sel["gap_rate_pct"]) == Decimal("50.00")
        assert join["below_target_count"] == 0
        assert Decimal(join["avg_competency_pct"]) == Decimal("100.00")
        # worst gap first + weakest list limited to flagged concepts
        assert body["concepts"][0]["concept_code"] == "SQL-SELECT"
        assert [c["concept_code"] for c in body["weakest_concepts"]] == ["SQL-SELECT"]

    def test_empty_cohort(self, client, db_session, admin):
        r = client.get(
            f"{BASE}/analytics/cohort",
            headers={"Authorization": f"Bearer {admin['token']}"},
        )
        assert r.status_code == 200
        assert r.json() == {
            "learner_count": 0,
            "finalized_sessions": 0,
            "concepts": [],
            "weakest_concepts": [],
        }

    def test_latest_session_per_learner_dedupes_resits(
        self, client, db_session, admin
    ):
        """A resit learner contributes only their latest result."""
        adm, l1, l2, c_sel, c_join, a = _seed_cohort(db_session)
        # l2 resits and now scores 100% on SELECT → below count drops to 0
        s3 = _session(db_session, l2, a)
        _score(db_session, s3, l2, c_sel, "4.0", 1)
        db_session.commit()

        r = client.get(
            f"{BASE}/analytics/cohort",
            headers={"Authorization": f"Bearer {admin['token']}"},
        )
        sel = next(
            c for c in r.json()["concepts"] if c["concept_code"] == "SQL-SELECT"
        )
        assert sel["learners_assessed"] == 2
        assert Decimal(sel["avg_competency_pct"]) == Decimal("100.00")
        assert sel["below_target_count"] == 0

    def test_assessment_filter_and_404(self, client, db_session, admin):
        _seed_cohort(db_session)
        h = {"Authorization": f"Bearer {admin['token']}"}
        ok = client.get(
            f"{BASE}/analytics/cohort?assessment_id=999999", headers=h
        )
        assert ok.status_code == 404

    def test_in_progress_sessions_excluded(self, client, db_session, admin):
        _, l1, _, _, _, a = _seed_cohort(db_session)
        _session(db_session, l1, a, status="in_progress")  # live session
        db_session.commit()
        r = client.get(f"{BASE}/analytics/cohort",
                       headers={"Authorization": f"Bearer {admin['token']}"})
        assert r.json()["finalized_sessions"] == 2


class TestLearnerDrilldown:
    def test_learner_roster(self, client, db_session, admin):
        _, l1, l2, *_ = _seed_cohort(db_session)
        r = client.get(
            f"{BASE}/learners",
            headers={"Authorization": f"Bearer {admin['token']}"},
        )
        assert r.status_code == 200
        rows = {row["email"]: row for row in r.json()}
        assert set(rows) == {"l1@test.dev", "l2@test.dev"}
        assert rows["l1@test.dev"]["sessions_completed"] == 1
        assert rows["l1@test.dev"]["full_name"] == "One"

    def test_learner_sessions(self, client, db_session, admin):
        _, l1, _, c_sel, _, _ = _seed_cohort(db_session)
        r = client.get(
            f"{BASE}/learners/{l1.account_id}/sessions",
            headers={"Authorization": f"Bearer {admin['token']}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == "l1@test.dev"
        assert len(body["sessions"]) == 1
        assert body["sessions"][0]["status"] == "completed"
        assert body["sessions"][0]["answered_count"] == 2

    def test_learner_sessions_404_for_admin_id(
        self, client, db_session, admin
    ):
        adm = db_session.query(Account).filter_by(email="admin@test.dev").one()
        r = client.get(
            f"{BASE}/learners/{adm.account_id}/sessions",
            headers={"Authorization": f"Bearer {admin['token']}"},
        )
        assert r.status_code == 404

    def test_admin_reads_session_competency(self, client, db_session, admin):
        _, l1, _, c_sel, c_join, _ = _seed_cohort(db_session)
        session = (
            db_session.query(AssessmentSession)
            .filter_by(learner_id=l1.account_id)
            .one()
        )
        r = client.get(
            f"{BASE}/sessions/{session.session_id}/competency",
            headers={"Authorization": f"Bearer {admin['token']}"},
        )
        assert r.status_code == 200
        concepts = {c["concept_code"]: c for c in r.json()["concepts"]}
        assert Decimal(concepts["SQL-SELECT"]["competency_pct"]) == Decimal("100.00")
        assert Decimal(concepts["SQL-JOIN"]["target_pct"]) == Decimal("60.00")

    def test_admin_competency_409_live_404_missing(
        self, client, db_session, admin
    ):
        h = {"Authorization": f"Bearer {admin['token']}"}
        assert client.get(
            f"{BASE}/sessions/999999/competency", headers=h
        ).status_code == 404

        _, l1, _, _, _, a = _seed_cohort(db_session)
        live = _session(db_session, l1, a, status="in_progress")
        # still within its window — expires_at is in the future
        live.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        live.submitted_at = None
        db_session.commit()
        r = client.get(
            f"{BASE}/sessions/{live.session_id}/competency", headers=h
        )
        assert r.status_code == 409
