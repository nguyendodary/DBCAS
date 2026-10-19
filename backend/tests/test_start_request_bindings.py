"""Browser-reproduced resume UUID retries must never create a second exam."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.db import get_session_factory
from app.models import AssessmentSession, SessionStartRequest
from app.schemas import PersonalizedStartRequest
from app.services.personalized_assessment import start_session
from test_adaptive_engine import _make_account
from test_supervisor_requirements import started, headers, complete


@pytest.mark.parametrize("ending", ["completed", "timed_out"])
def test_resume_request_survives_finalization(client, db_session, ending):
    _, learner, _, assessment, first, original = started(client, db_session, skills=1)
    payload = {**original, "request_id": str(uuid4())}
    route = f"/api/v1/assessments/{assessment.assessment_id}/sessions"
    resumed = client.post(route, headers=headers(learner), json=payload)
    assert resumed.status_code == 201
    assert resumed.json()["session_id"] == first["session_id"]
    if ending == "completed":
        complete(client, db_session, learner, resumed.json())
    else:
        session = db_session.get(AssessmentSession, first["session_id"])
        session.expires_at -= timedelta(hours=2)
        db_session.commit()
    for request in (payload, original):
        retry = client.post(route, headers=headers(learner), json=request)
        assert retry.status_code == 201
        assert retry.json()["session_id"] == first["session_id"]
        assert retry.json()["status"] == ending
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 1
    assert db_session.scalar(select(func.count()).select_from(SessionStartRequest)) == 2
    db_session.expire_all()
    assert db_session.get(AssessmentSession, first["session_id"]).start_request_id == original["request_id"]


def test_resume_request_rejects_changed_selection_and_assessment(client, db_session):
    _, learner, _, a, first, original = started(client, db_session, skills=1)
    payload = {**original, "request_id": str(uuid4())}
    route = f"/api/v1/assessments/{a.assessment_id}/sessions"
    assert client.post(route, headers=headers(learner), json=payload).status_code == 201
    for aid, request in ((a.assessment_id, {**payload, "difficulty": "HARD"}),
                         (a.assessment_id + 9999, payload)):
        response = client.post(f"/api/v1/assessments/{aid}/sessions", headers=headers(learner), json=request)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "start_request_conflict"
    assert db_session.scalar(select(func.count()).select_from(SessionStartRequest)) == 2


def test_concurrent_resume_requests_are_bound_once_per_uuid(client, db_session):
    _, learner, _, a, first, original = started(client, db_session, skills=1)
    requests = [PersonalizedStartRequest(**{**original, "request_id": str(uuid4())}) for _ in range(3)]
    def resume(payload):
        with get_session_factory()() as db:
            return start_session(db, a.assessment_id, learner, payload).session_id
    with ThreadPoolExecutor(max_workers=4) as executor:
        assert set(executor.map(resume, requests + requests)) == {first["session_id"]}
    complete(client, db_session, learner, first)
    with ThreadPoolExecutor(max_workers=4) as executor:
        assert set(executor.map(resume, requests)) == {first["session_id"]}
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 1
    assert db_session.scalar(select(func.count()).select_from(SessionStartRequest)) == 4


def test_request_ids_are_scoped_to_authenticated_learner(client, db_session):
    _, learner, _, a, first, original = started(client, db_session, skills=1)
    other = _make_account(db_session, "other-binding@test.dev", "Learner")
    response = client.post(f"/api/v1/assessments/{a.assessment_id}/sessions", headers=headers(other), json=original)
    assert response.status_code == 201
    assert response.json()["session_id"] != first["session_id"]
    assert db_session.scalar(select(func.count()).select_from(SessionStartRequest)) == 2


def test_binding_database_rejects_cross_owner_and_reassignment(client, db_session):
    from sqlalchemy import text
    _, learner, _, _, first, original = started(client, db_session, skills=1)
    other = _make_account(db_session, "wrong-binding@test.dev", "Learner")
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(SessionStartRequest(learner_id=other.account_id, request_id=str(uuid4()), session_id=first["session_id"]))
            db_session.flush()
    for statement in ("UPDATE session_start_request SET request_id='different'", "DELETE FROM session_start_request"):
        with pytest.raises(ProgrammingError, match="immutable"):
            with db_session.begin_nested():
                db_session.execute(text(statement))


def test_migration_backfills_only_known_requests_without_changing_sessions():
    import psycopg
    from app.config import ROOT_DIR, get_settings
    namespace = "bindings_" + uuid4().hex[:12]
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            conn.execute((ROOT_DIR / "db/schema.sql").read_text(encoding="utf-8").split("-- 010_session_start_request_bindings.sql")[0], prepare=False)
            conn.execute("INSERT INTO account(email,password_hash) VALUES ('binding@migration.test','not-a-login-hash')")
            conn.execute("INSERT INTO assessment(title,created_by) VALUES ('Preserved',1)")
            request_id = str(uuid4())
            for rid in (request_id, None):
                conn.execute("INSERT INTO assessment_session(assessment_id,learner_id,expires_at,start_request_id) VALUES (1,1,NOW()+INTERVAL '1 hour',%s)", (rid,))
            before = conn.execute("SELECT to_jsonb(s) FROM assessment_session s ORDER BY session_id").fetchall()
            sql = (ROOT_DIR / "db/migrations/010_session_start_request_bindings.sql").read_text(encoding="utf-8")
            conn.execute(sql, prepare=False)
            conn.execute(sql, prepare=False)
            assert conn.execute("SELECT learner_id,request_id,session_id FROM session_start_request").fetchall() == [(1, request_id, 1)]
            assert conn.execute("SELECT to_jsonb(s) FROM assessment_session s ORDER BY session_id").fetchall() == before
        finally:
            conn.execute("SET search_path TO public")
            conn.execute(f'DROP SCHEMA "{namespace}" CASCADE')
