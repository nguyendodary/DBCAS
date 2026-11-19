"""PR 3B-2: FIXED TEST sessions finalize an OFFICIAL v1 result.

Covers finalize idempotency, the version/publication/pointer chain, 026
trigger completeness (including essay criteria), cumulative competency
reading the current version, and LEGACY/ADAPTIVE/PRACTICE regressions.
"""
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
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
    # 3B-3: an OFFICIAL v1 inside the 7-day window is immediately eligible.
    assert body["can_request_review"] is True
    assert body["review_window_expires_at"] is not None


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


def _prepare_fixed_paper(client, db_session, learner, concepts):
    state = _start(client, db_session, learner, concepts)
    sid = state["session_id"]
    auth = headers(learner)
    for attempt in db_session.scalars(
        select(Attempt).where(Attempt.session_id == sid)
    ):
        saved = _save(client, sid, auth, attempt.seq_no, 1,
                      _answer(attempt.question_snapshot, correct=True))
        assert saved.status_code == 200, saved.text
    db_session.expire_all()
    return sid, auth


def test_fixed_legacy_cumulative_reads_attempt_score(client, db_session):
    """A FIXED session explicitly kept on LEGACY never consults a version."""
    _, learner, concepts = fixture(db_session)
    sid, auth = _prepare_fixed_paper(client, db_session, learner, concepts)
    session = db_session.get(AssessmentSession, sid)
    session.review_policy = "LEGACY"
    db_session.commit()
    db_session.expire_all()

    submitted = client.post(SUBMIT.format(sid=sid), headers=auth, json={})
    assert submitted.status_code == 200, submitted.text
    assert _version(db_session, sid) is None

    now = datetime.now(timezone.utc)
    for attempt in db_session.scalars(
        select(Attempt).where(Attempt.session_id == sid)
    ):
        attempt.submitted_at = now
        attempt.score = Decimal("1.00")
        attempt.grading_status = "graded"
    session = db_session.get(AssessmentSession, sid)
    session.release_status = "published"
    session.published_at = now
    db_session.commit()
    db_session.expire_all()

    def earned(body):
        return sum((Decimal(str(item["points_earned"]))
                    for item in body["concepts"]), Decimal(0))

    before = client.get(CUMULATIVE, headers=auth).json()
    assert before["summary"]["finalized_assessments"] == 1
    first = db_session.scalar(
        select(Attempt).where(Attempt.session_id == sid).order_by(Attempt.seq_no))
    first.score = Decimal("0.00")
    db_session.commit()
    db_session.expire_all()
    after = client.get(CUMULATIVE, headers=auth).json()
    assert earned(after) == earned(before) - Decimal("1.00")


def test_finalized_fixed_without_v1_is_not_official(client, db_session, monkeypatch):
    """No v1 means no current OFFICIAL version to read; stay out of cumulative."""
    import app.services.result_version as versions

    _, learner, concepts = fixture(db_session)
    sid, auth = _prepare_fixed_paper(client, db_session, learner, concepts)
    monkeypatch.setattr(versions, "ensure_official_v1", lambda db, session: None)
    submitted = client.post(SUBMIT.format(sid=sid), headers=auth, json={})
    assert submitted.status_code == 200, submitted.text
    db_session.expire_all()

    session = db_session.get(AssessmentSession, sid)
    assert session.status == "completed"
    assert session.review_policy == "AI_OFFICIAL_REVIEW"
    assert session.current_result_version_id is None
    assert _version(db_session, sid) is None
    profile = client.get(CUMULATIVE, headers=auth).json()
    assert profile["summary"]["finalized_assessments"] == 0
    assert profile["concepts"] == []


def test_concurrent_finalize_waits_on_row_lock(client, db_session):
    """The second caller blocks on SELECT FOR UPDATE and then sees a final session."""
    from app.db import get_session_factory
    from app.repositories import AssessmentRepository

    _, learner, concepts = fixture(db_session)
    sid, _ = _prepare_fixed_paper(client, db_session, learner, concepts)
    # Hold the session row lock in this transaction; a second transaction
    # cannot finalize until it is released.
    assert AssessmentRepository(db_session).lock_session(sid) is not None

    started, finished, outcome = threading.Event(), threading.Event(), {}

    def second_caller():
        db = get_session_factory()()
        started.set()
        try:
            finalize(db, db.get(AssessmentSession, sid))
            outcome["ok"] = True
        except Exception as exc:  # pragma: no cover - surfaced by assertions
            outcome["error"] = repr(exc)
        finally:
            db.close()
            finished.set()

    worker = threading.Thread(target=second_caller, daemon=True)
    worker.start()
    assert started.wait(5)
    assert not finished.wait(2), "second finalize did not wait on the row lock"
    db_session.rollback()  # release the lock
    assert finished.wait(30), "second finalize never completed"
    worker.join()
    assert outcome.get("ok"), outcome
    db_session.expire_all()
    assert _count(db_session, SessionResultVersion, sid) == 1
    assert _count(db_session, SessionResultPublication, sid) == 1


def test_v1_failure_rolls_back_and_has_no_silent_retry(client, db_session, monkeypatch):
    """A failed v1 write rolls back finalize; a later call retries explicitly."""
    import app.services.result_version as versions

    _, learner, concepts = fixture(db_session)
    sid, _ = _prepare_fixed_paper(client, db_session, learner, concepts)

    def fail(db, session):
        raise RuntimeError("v1 unavailable")

    monkeypatch.setattr(versions, "ensure_official_v1", fail)
    with pytest.raises(RuntimeError, match="v1 unavailable"):
        finalize(db_session, db_session.get(AssessmentSession, sid))
    db_session.rollback()
    db_session.expire_all()
    assert db_session.get(AssessmentSession, sid).status == "in_progress"
    assert _version(db_session, sid) is None
    assert _count(db_session, SessionResultPublication, sid) == 0

    monkeypatch.undo()  # no automatic retry inside finalize
    finalize(db_session, db_session.get(AssessmentSession, sid))
    db_session.expire_all()
    assert _version(db_session, sid) is not None
