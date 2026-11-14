"""Learner final-result contracts for both snapshot writers.

Existing API tests only exercised new-style administrator snapshots, whose
metric fields are decimal strings, while migration tests inspected the legacy
020 row directly in SQL without passing it through FastAPI serialization.
These tests run the real migration-020 backfill over a populated published
practice session, then read it through the learner endpoint.
"""
from datetime import datetime, timezone

import psycopg
from sqlalchemy import select

from app.config import ROOT_DIR, get_settings
from app.models import AssessmentSession, ResultReleaseEvent, SessionFinalResult
from app.services import evaluation_service as evaluations
from test_learner_practice import complete, fixture, selection
from test_supervisor_requirements import headers


def _start_and_complete(client, db, learner, concepts):
    state = client.post(
        "/api/v1/practice/start", headers=headers(learner),
        json=selection(concepts),
    )
    assert state.status_code == 200, state.text
    completed = complete(client, db, learner, state.json())
    assert completed["status"] == "completed"
    assert evaluations.process_one(db, force_fallback=True)
    return state.json()["session_id"]


def _publish_legacy(db, session_id, reviewer_id):
    session = db.get(AssessmentSession, session_id)
    session.release_status = "published"
    session.published_at = datetime.now(timezone.utc)
    session.review_revision = 1
    db.add(ResultReleaseEvent(
        session_id=session_id,
        previous_status="pending_review",
        new_status="published",
        reviewer_id=reviewer_id,
    ))
    db.commit()

    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(
            (ROOT_DIR / "db/migrations/020_provisional_ai_final_results.sql").read_text(),
            prepare=False,
        )
    db.expire_all()


def test_legacy_020_backfill_serializes_as_final_result(client, db_session):
    admin, learner, concepts = fixture(db_session)
    session_id = _start_and_complete(client, db_session, learner, concepts)
    _publish_legacy(db_session, session_id, admin.account_id)

    final = db_session.scalar(select(SessionFinalResult).where(
        SessionFinalResult.session_id == session_id))
    assert final is not None and final.source == "legacy"
    assert final.overall["earned"] == 3.0 and final.overall["possible"] == 3.0

    response = client.get(
        f"/api/v1/evaluations/attempts/{session_id}", headers=headers(learner))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["final"] is True and body["provisional"] is False
    assert body["source"] == "legacy_admin_approved"
    assert body["score"] == {
        "earned": "3.00", "possible": "3.00", "percentage": 100.0}
    assert body["question_results"]
    assert all(isinstance(item["score"], float) for item in body["question_results"])
    assert all(isinstance(item["points"], float) for item in body["question_results"])
    assert "ai_evaluation" not in response.text


def test_new_admin_snapshot_serializes_as_final_result(client, db_session):
    admin, learner, concepts = fixture(db_session)
    session_id = _start_and_complete(client, db_session, learner, concepts)
    review_path = f"/api/v1/admin/grading-reviews/{session_id}"
    detail = client.get(review_path, headers=headers(admin))
    assert detail.status_code == 200, detail.text
    published = client.post(
        review_path + "/publish", headers=headers(admin),
        json={"revision": detail.json()["revision"]},
    )
    assert published.status_code == 200, published.text

    response = client.get(
        f"/api/v1/evaluations/attempts/{session_id}", headers=headers(learner))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["final"] is True and body["provisional"] is False
    assert body["source"] == "admin_approved"
    assert body["score"] == {
        "earned": "3.00", "possible": "3.00", "percentage": 100.0}
    assert "ai_evaluation" not in response.text
