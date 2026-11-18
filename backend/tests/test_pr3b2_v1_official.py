"""PR 3B-2: FIXED TEST sessions finalize an OFFICIAL v1 result.

Covers finalize idempotency, the version/publication/pointer chain, 026
trigger completeness (including essay criteria), cumulative competency
reading the current version, and LEGACY/ADAPTIVE/PRACTICE regressions.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.models import (
    AssessmentSession,
    Attempt,
    AttemptRubricCriterion,
    SessionResultCriterionScore,
    SessionResultPublication,
    SessionResultVersion,
    SessionResultVersionScore,
)
from app.services.assessment_lifecycle import finalize
from test_fixed_paper_api import _answer, _attempt, _save, _start
from test_learner_practice import _fixed_payload, complete, fixture, selection
from test_supervisor_requirements import headers

SUBMIT = "/api/v1/sessions/{sid}/paper/submit"
CUMULATIVE = "/api/v1/sessions/competency/cumulative"


def _finalize_fixed(client, db_session, *, payload=None):
    _, learner, concepts = fixture(db_session)
    if payload is None:
        state = _start(client, db_session, learner, concepts)
    else:
        response = client.post("/api/v1/practice/start", headers=headers(learner),
                               json=payload(concepts))
        assert response.status_code == 200, response.text
        state = response.json()
    sid = state["session_id"]
    auth = headers(learner)
    for attempt in db_session.scalars(
        select(Attempt).where(Attempt.session_id == sid)
    ):
        saved = _save(client, sid, auth, attempt.seq_no, 1,
                      _answer(attempt.question_snapshot, correct=True))
        assert saved.status_code == 200, saved.text
    submitted = client.post(SUBMIT.format(sid=sid), headers=auth, json={})
    assert submitted.status_code == 200, submitted.text
    db_session.expire_all()
    return learner, sid, submitted.json()


def _version(db_session, sid):
    return db_session.scalar(
        select(SessionResultVersion).where(SessionResultVersion.session_id == sid)
    )


def _count(db_session, model, sid):
    return db_session.scalar(
        select(func.count()).select_from(model).where(model.session_id == sid)
    )


def test_finalize_creates_v1_official_and_pointer(client, db_session):
    _, sid, body = _finalize_fixed(client, db_session)
    session = db_session.get(AssessmentSession, sid)
    assert session.review_policy == "AI_OFFICIAL_REVIEW"
    assert session.release_status == "published"

    version = _version(db_session, sid)
    assert version is not None
    assert version.version_no == 1 and version.source == "V1"
    assert session.current_result_version_id == version.result_version_id

    publication = db_session.get(SessionResultPublication, version.result_version_id)
    assert publication.state == "OFFICIAL" and publication.published_at is not None

    scores = list(db_session.scalars(
        select(SessionResultVersionScore).where(
            SessionResultVersionScore.session_id == sid,
            SessionResultVersionScore.result_version_id == version.result_version_id)
    ))
    assert len(scores) == 3 and all(row.source == "MACHINE" for row in scores)
    assert sum((row.score for row in scores), Decimal(0)) == version.total_score
    assert sum((row.max_score for row in scores), Decimal(0)) == version.max_score

    assert body["result_version"] == 1
    assert body["is_current"] is True
    assert body["review_status"] == "OFFICIAL"
    assert body["can_request_review"] is False


def test_finalize_is_idempotent(client, db_session):
    learner, sid, first = _finalize_fixed(client, db_session)
    again = client.post(SUBMIT.format(sid=sid), headers=headers(learner), json={})
    assert again.status_code == 200, again.text
    assert again.json()["result_version"] == first["result_version"]

    version = _version(db_session, sid)
    finalize(db_session, db_session.get(AssessmentSession, sid))
    db_session.expire_all()
    assert _count(db_session, SessionResultVersion, sid) == 1
    assert _count(db_session, SessionResultPublication, sid) == 1
    assert _count(db_session, SessionResultVersionScore, sid) == 3
    assert db_session.get(AssessmentSession, sid).current_result_version_id == (
        version.result_version_id)


def test_026_triggers_accept_complete_v1_with_essay_criteria(client, db_session):
    def with_essay(concepts):
        return {**_fixed_payload(concepts),
                "question_count": 1,
                "question_mix": {"mcq": 0, "sql": 0, "essay": 1},
                "difficulties": ["MEDIUM"]}

    _, sid, _ = _finalize_fixed(client, db_session, payload=with_essay)
    version = _version(db_session, sid)
    attempts = list(db_session.scalars(
        select(Attempt).where(Attempt.session_id == sid)))
    essays = [a for a in attempts if a.question_snapshot["question_type"] == "essay"]
    assert essays

    for attempt in essays:
        row = db_session.scalar(
            select(SessionResultVersionScore).where(
                SessionResultVersionScore.session_id == sid,
                SessionResultVersionScore.result_version_id == version.result_version_id,
                SessionResultVersionScore.attempt_id == attempt.attempt_id)
        )
        criteria = list(db_session.scalars(
            select(SessionResultCriterionScore).where(
                SessionResultCriterionScore.session_id == sid,
                SessionResultCriterionScore.result_version_id == version.result_version_id,
                SessionResultCriterionScore.attempt_id == attempt.attempt_id)
        ))
        assert criteria and len(criteria) == _count(
            db_session, AttemptRubricCriterion, sid)
        assert sum((c.score for c in criteria), Decimal(0)) == row.score
        assert sum((c.max_points for c in criteria), Decimal(0)) == row.max_score
        snapshots = list(db_session.scalars(
            select(AttemptRubricCriterion).where(
                AttemptRubricCriterion.attempt_id == attempt.attempt_id)
        ))
        assert all(s.profile_snapshot_hash
                   == attempt.question_snapshot["rubric_snapshot_hash"]
                   for s in snapshots)


def test_cumulative_reads_current_version_not_attempt_score(client, db_session):
    learner, sid, _ = _finalize_fixed(client, db_session)
    auth = headers(learner)
    before = client.get(CUMULATIVE, headers=auth).json()
    assert before["summary"]["finalized_assessments"] == 1

    now = datetime.now(timezone.utc)
    for attempt in db_session.scalars(
        select(Attempt).where(Attempt.session_id == sid)
    ):
        attempt.score = Decimal("999.99")
        attempt.grading_status = "graded"
        attempt.submitted_at = now
    db_session.commit()
    db_session.expire_all()

    after = client.get(CUMULATIVE, headers=auth).json()
    assert after == before


def test_practice_and_adaptive_stay_legacy(client, db_session):
    _, learner, concepts = fixture(db_session)
    state = client.post("/api/v1/practice/start", headers=headers(learner),
                        json=selection(concepts))
    assert state.status_code == 200, state.text
    sid = state.json()["session_id"]
    complete(client, db_session, learner, state.json())
    db_session.expire_all()
    session = db_session.get(AssessmentSession, sid)
    assert session.review_policy == "LEGACY"
    assert session.current_result_version_id is None
    assert _version(db_session, sid) is None

    from app.repositories import AssessmentRepository
    adaptive = AssessmentRepository(db_session).create_session(
        None, learner.account_id,
        datetime.now(timezone.utc) + timedelta(hours=1),
        purpose="TEST",
    )
    adaptive.config_snapshot = {
        "purpose": "TEST", "assembly_mode": "ADAPTIVE", "runner_mode": "adaptive",
    }
    db_session.commit()
    assert adaptive.review_policy == "LEGACY"
    finalize(db_session, adaptive)
    db_session.expire_all()
    assert _version(db_session, adaptive.session_id) is None
