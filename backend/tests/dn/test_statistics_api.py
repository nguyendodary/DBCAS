"""Learner privacy, cohort statistics and published evidence on real PostgreSQL."""
from decimal import Decimal

from app.models import CloConcept, CourseLearningOutcome
from app.repositories import AssessmentRepository
from app.services.evidence_context import capture_question
from test_admin_questions import _admin
from test_competency import _make_learner, _make_concept, _make_session, _add_question, _add_attempt


def _login(client, email):
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Secret123!"}).json()["access_token"]
    return {"Authorization": "Bearer " + token}


def evidence_fixture(client, db):
    admin_headers = _admin(client, db)
    learner = _make_learner(db)
    other = _make_learner(db, "other@dn.test")
    sql = _make_concept(db, "DN-SQL", area="SQL")
    index = _make_concept(db, "DN-INDEX", area="Index")
    clo = CourseLearningOutcome(clo_code="DN-CLO", title="SQL querying", created_by=learner.account_id)
    db.add(clo)
    db.flush()
    db.add(CloConcept(clo_id=clo.clo_id, concept_id=sql.concept_id, status="confirmed"))
    first = _make_session(db, learner, targets={sql: 90})
    second = _make_session(db, learner, targets={index: 80})
    q1 = _add_question(db, learner.account_id, points="10", concept_ids=[sql.concept_id])
    q2 = _add_question(db, learner.account_id, points="2", concept_ids=[index.concept_id])
    q2.difficulty_level = 3
    a1 = _add_attempt(db, first, q1, 1, score=8)
    a2 = _add_attempt(db, second, q2, 1, score=1)
    third = _make_session(db, other)
    a3 = _add_attempt(db, third, q1, 1, score=10)
    practice = _make_session(db, learner)
    practice.assessment_id = None
    practice.release_status = "provisional_ai"
    practice.config_snapshot = {"learner_defined": True, "assembly_mode": "PRACTICE"}
    _add_attempt(db, practice, q1, 1, score=10)
    withheld = _make_session(db, learner)
    withheld.release_status = "pending_review"
    _add_attempt(db, withheld, q1, 1, score=0)
    repo = AssessmentRepository(db)
    for attempt, question in ((a1, q1), (a2, q2), (a3, q1)):
        attempt.question_snapshot = capture_question(repo, question)
    db.commit()
    return learner, other, first, admin_headers


def test_learner_dashboard_is_owned_and_only_published_formal(client, db_session):
    learner, other, first, admin = evidence_fixture(client, db_session)
    headers = _login(client, learner.email)
    response = client.get(f"/api/v1/sessions/statistics?learner_id={other.account_id}&limit=1", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["learner_id"] == learner.account_id
    assert Decimal(body["dimensions"]["overall"]["competency_pct"]) == 75
    assert body["published_formal_sessions"] == 2 and body["progress_total"] == 2
    assert body["pending_formal_sessions"] == 2
    assert len(body["progress"]) == 1 and body["ranking"] == []
    assert body["dimensions"]["clos"][0]["label"].startswith("DN-CLO")
    assert body["dimensions"]["clo_mapping_unknown_attempts"] == 0
    assert sum(b["count"] for b in body["score_distribution"]) == 2
    assert [s["topic"] for s in body["recommendations"]] == ["Index", "SQL"]
    assert Decimal(body["recommendations"][0]["maximum_shortfall_pct"]) == 30
    assert all(p["learner_id"] == learner.account_id for p in body["progress"])
    scoped = client.get(f"/api/v1/sessions/statistics?assessment_id={first.assessment_id}", headers=headers).json()
    assert scoped["progress_total"] == 1
    assert scoped["pending_formal_sessions"] == 0
    assert Decimal(scoped["dimensions"]["overall"]["competency_pct"]) == 80
    assert client.get("/api/v1/admin/analytics/statistics", headers=headers).status_code == 403
    assert client.get("/api/v1/sessions/statistics", headers=admin).status_code == 403


def test_learner_rank_never_exposes_another_learner_or_accepts_an_identity_override(client, db_session):
    learner, other, first, admin = evidence_fixture(client, db_session)
    headers = _login(client, learner.email)
    response = client.get(f"/api/v1/sessions/ranking?learner_id={other.account_id}", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"rank": 2, "participants": 2, "competency_pct": "75.00"}
    assert client.get('/api/v1/sessions/ranking', headers=admin).status_code == 403
    assert client.get('/api/v1/sessions/ranking').status_code == 401
    assert client.get('/api/v1/sessions/ranking?assessment_id=0', headers=headers).status_code == 422
    assert client.get('/api/v1/sessions/ranking?assessment_id=99999', headers=headers).status_code == 404


def test_learner_rank_is_unavailable_without_published_evidence(client, db_session):
    learner = _make_learner(db_session)
    response = client.get('/api/v1/sessions/ranking', headers=_login(client, learner.email))
    assert response.json() == {"rank": None, "participants": 0, "competency_pct": None}


def test_administrator_distribution_ranking_filtering_and_bounds(client, db_session):
    learner, other, first, headers = evidence_fixture(client, db_session)
    body = client.get("/api/v1/admin/analytics/statistics", headers=headers).json()
    assert body["progress_total"] == 3
    assert body["pending_formal_sessions"] == 2
    assert [(r["learner_id"], r["rank"]) for r in body["ranking"]] == [(other.account_id, 1), (learner.account_id, 2)]
    assert body["score_distribution"][-1]["count"] == 2  # 80 and 100 are included once.
    selected = client.get(f"/api/v1/admin/analytics/statistics?learner_id={learner.account_id}&offset=1&limit=1", headers=headers).json()
    assert selected["learner_id"] == learner.account_id and len(selected["progress"]) == 1
    assert len(selected["recommendations"]) == 2
    for suffix, status in (("limit=0", 422), ("limit=501", 422), ("offset=-1", 422),
                           ("assessment_id=-1", 422), ("assessment_id=999999", 404), ("learner_id=999999", 404)):
        assert client.get("/api/v1/admin/analytics/statistics?" + suffix, headers=headers).status_code == status
    assert client.get("/api/v1/admin/analytics/statistics").status_code == 401


def test_unassessed_learner_has_no_invented_zero(client, db_session):
    learner = _make_learner(db_session)
    body = client.get("/api/v1/sessions/statistics", headers=_login(client, learner.email)).json()
    assert body["dimensions"]["overall"]["competency_pct"] is None
    assert body["dimensions"]["clos"] == [] and body["progress"] == []
    assert body["recommendations"] == [] and body["progress_total"] == 0
    assert body["pending_formal_sessions"] == 0
    assert all(b["count"] == 0 for b in body["score_distribution"])
