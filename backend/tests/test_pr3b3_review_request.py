"""PR 3B-3: learner review requests, administrator queue, claim lease, REJECT.

The official v1 result is never mutated in this PR: it only records intent,
leases the case and supports the REJECT branch. v2 regrading is 3B-5.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.main import app
from app.models import (
    AccountRole,
    AssessmentSession,
    Attempt,
    ReviewRequest,
    Role,
    SessionResultPublication,
    SessionResultVersion,
)
from app.services.review_flow import reclaim_and_expire
from test_admin_analytics import _make_account
from test_fixed_paper_api import _answer, _save, _start
from test_learner_practice import fixture
from test_pr3b2_v1_official import _finalize_fixed
from test_supervisor_requirements import headers

REVIEW = "/api/v1/sessions/{sid}/review-request"
QUEUE = "/api/v1/admin/review-requests"
SUBMIT = "/api/v1/sessions/{sid}/paper/submit"


def _request(client, learner, sid, *, key=None, reason="Please review my official result."):
    return client.post(
        REVIEW.format(sid=sid),
        headers={**headers(learner), "Idempotency-Key": str(key or uuid4())},
        json={"reason": reason},
    )


def _case(db_session, sid):
    return db_session.scalar(select(ReviewRequest).where(ReviewRequest.session_id == sid))


def _publication(db_session, sid):
    version = db_session.scalar(
        select(SessionResultVersion).where(SessionResultVersion.session_id == sid)
    )
    return db_session.get(SessionResultPublication, version.result_version_id)


def test_request_once_visibility_idempotency_and_queue(client, db_session):
    learner, sid, body = _finalize_fixed(client, db_session)
    assert body["can_request_review"] is True
    assert body["review_window_expires_at"] is not None
    admin = _make_account(db_session, "review-admin@test.dev", "Administrator")
    other = _make_account(db_session, "review-other@test.dev", "Learner")
    key = uuid4()
    first = _request(client, learner, sid, key=key)
    assert first.status_code == 201, first.text
    case = first.json()
    assert case["status"] == "REQUESTED" and case["origin"] == "LEARNER"
    assert case["window_expires_at"] is not None
    assert case["v2_state"] == "NONE"
    private_fields = {"claimed_by", "resolved_by", "resolution_note", "analysis_status"}
    assert private_fields.isdisjoint(case)

    owner = client.get(REVIEW.format(sid=sid), headers=headers(learner))
    assert owner.status_code == 200
    assert owner.json()["review_request_id"] == case["review_request_id"]
    assert owner.json()["v2_state"] == "NONE"
    assert private_fields.isdisjoint(owner.json())
    admin_view = client.get(REVIEW.format(sid=sid), headers=headers(admin, "Administrator"))
    assert admin_view.status_code == 200
    assert {"claimed_by", "resolved_by", "resolution_note"} <= admin_view.json().keys()
    assert "v2_state" not in admin_view.json()
    assert client.get(REVIEW.format(sid=sid), headers=headers(other)).status_code == 403
    assert client.get(REVIEW.format(sid=sid + 1000), headers=headers(other)).status_code == 404

    replay = _request(client, learner, sid, key=key)
    assert replay.status_code == 200
    assert replay.json()["review_request_id"] == case["review_request_id"]
    assert replay.json()["v2_state"] == "NONE"
    assert private_fields.isdisjoint(replay.json())
    duplicate = _request(client, learner, sid)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "review_exists"

    queue = client.get(QUEUE, headers=headers(admin, "Administrator"))
    assert queue.status_code == 200
    assert [row["review_request_id"] for row in queue.json()] == [case["review_request_id"]]
    assert queue.json()[0]["learner_email"] == learner.email
    empty = client.get(QUEUE + "?status=REJECTED", headers=headers(admin, "Administrator"))
    assert empty.json() == []
    assert client.get(QUEUE, headers=headers(learner)).status_code == 403

    state = client.get(f"/api/v1/sessions/{sid}", headers=headers(learner)).json()
    assert state["review_status"] == "REQUESTED"
    assert state["can_request_review"] is False


@pytest.mark.parametrize(
    "offset_seconds,expected", [(60, 201), (-60, 409)], ids=["inside", "closed"]
)
def test_window_boundary_uses_server_clock(client, db_session, offset_seconds, expected):
    learner, sid, _ = _finalize_fixed(client, db_session)
    publication = _publication(db_session, sid)
    publication.published_at = (
        datetime.now(timezone.utc) - timedelta(days=7) + timedelta(seconds=offset_seconds)
    )
    db_session.commit()
    response = _request(client, learner, sid)
    assert response.status_code == expected, response.text
    if expected == 409:
        assert response.json()["error"]["code"] == "review_window_closed"


def test_concurrent_same_key_creates_one_case(client, db_session):
    learner, sid, _ = _finalize_fixed(client, db_session)
    key = str(uuid4())

    def fire(_):
        return _request(client, learner, sid, key=key)

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(fire, range(2)))
    assert sorted(response.status_code for response in responses) == [200, 201]
    assert len({response.json()["review_request_id"] for response in responses}) == 1
    assert db_session.scalar(
        select(func.count()).select_from(ReviewRequest).where(ReviewRequest.session_id == sid)
    ) == 1


def test_claim_reject_keeps_v1_and_guards_claim_holder(client, db_session):
    learner, sid, _ = _finalize_fixed(client, db_session)
    admin = _make_account(db_session, "review-admin@test.dev", "Administrator")
    second = _make_account(db_session, "review-admin2@test.dev", "Administrator")
    case = _request(client, learner, sid).json()
    h = headers(admin, "Administrator")
    claim = client.post(f"{QUEUE}/{case['review_request_id']}/claim", headers=h,
                        json={"expected_revision": case["revision"]})
    assert claim.status_code == 200, claim.text
    claimed = claim.json()
    assert claimed["status"] == "IN_REVIEW"
    assert claimed["claimed_by"] == admin.account_id
    assert claimed["claim_expires_at"] > claimed["claimed_at"]

    stale = client.post(f"{QUEUE}/{case['review_request_id']}/claim", headers=h,
                        json={"expected_revision": case["revision"]})
    assert stale.status_code == 409
    not_holder = client.post(
        f"{QUEUE}/{case['review_request_id']}/decision",
        headers=headers(second, "Administrator"),
        json={"expected_revision": claimed["revision"], "outcome": "REJECT",
              "note": "Second administrator tried to decide."})
    assert not_holder.status_code == 409
    assert not_holder.json()["error"]["code"] == "review_claim_required"

    pointer = db_session.get(AssessmentSession, sid).current_result_version_id
    reject = client.post(
        f"{QUEUE}/{case['review_request_id']}/decision", headers=h,
        json={"expected_revision": claimed["revision"], "outcome": "REJECT",
              "note": "The official result is correct after checking the rubric."})
    assert reject.status_code == 200, reject.text
    assert reject.json()["status"] == "REJECTED"
    assert reject.json()["resolved_by"] == admin.account_id

    db_session.expire_all()
    session = db_session.get(AssessmentSession, sid)
    assert session.current_result_version_id == pointer
    assert db_session.scalar(
        select(func.count()).select_from(SessionResultVersion).where(
            SessionResultVersion.session_id == sid)
    ) == 1
    assert db_session.scalar(
        select(func.count()).select_from(SessionResultVersion).where(
            SessionResultVersion.session_id == sid,
            SessionResultVersion.source == "V2")
    ) == 0
    assert db_session.get(ReviewRequest, case["review_request_id"]).status == "REJECTED"
    # Terminal cases cannot be requested again.
    assert _request(client, learner, sid).status_code == 409


def test_worker_reclaims_lease_and_expires_old_cases(client, db_session):
    learner, sid, _ = _finalize_fixed(client, db_session)
    admin = _make_account(db_session, "review-admin@test.dev", "Administrator")
    case = _request(client, learner, sid).json()
    h = headers(admin, "Administrator")
    claimed = client.post(f"{QUEUE}/{case['review_request_id']}/claim", headers=h,
                          json={"expected_revision": case["revision"]}).json()
    row = db_session.get(ReviewRequest, case["review_request_id"])
    row.claim_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()
    reclaimed = reclaim_and_expire(db_session, now=datetime.now(timezone.utc))
    db_session.commit()
    db_session.refresh(row)
    assert reclaimed["reclaimed"] == 1
    assert row.status == "REQUESTED" and row.claimed_by is None
    refreshed = db_session.get(ReviewRequest, case["review_request_id"])
    again = client.post(f"{QUEUE}/{case['review_request_id']}/claim", headers=h,
                        json={"expected_revision": refreshed.revision})
    assert again.status_code == 200, again.text

    expired = reclaim_and_expire(
        db_session, now=datetime.now(timezone.utc) + timedelta(days=31))
    db_session.commit()
    db_session.refresh(row)
    assert expired["expired"] == 1
    assert row.status == "EXPIRED"
    assert row.claimed_by is None
    assert _request(client, learner, sid).status_code == 409


def test_self_review_forbidden_even_with_both_roles(client, db_session):
    learner, sid, _ = _finalize_fixed(client, db_session)
    role = db_session.scalar(select(Role).where(Role.role_name == "Administrator"))
    db_session.add(AccountRole(account_id=learner.account_id, role_id=role.role_id))
    db_session.commit()
    case = _request(client, learner, sid).json()
    h = headers(learner, "Administrator")
    own_view = client.get(REVIEW.format(sid=sid), headers=h)
    assert own_view.status_code == 200
    assert own_view.json()["v2_state"] == "NONE"
    assert {"claimed_by", "resolved_by", "resolution_note"}.isdisjoint(own_view.json())
    claim = client.post(f"{QUEUE}/{case['review_request_id']}/claim", headers=h,
                        json={"expected_revision": case["revision"]})
    assert claim.status_code == 403
    assert claim.json()["error"]["code"] == "self_review_forbidden"


def _bare_session(db, learner, *, purpose="TEST", review_policy="LEGACY", assembly="FIXED"):
    now = datetime.now(timezone.utc)
    session = AssessmentSession(
        assessment_id=None,
        learner_id=learner.account_id,
        status="completed",
        purpose=purpose,
        purpose_source="SERVER",
        locale="en",
        expires_at=now + timedelta(hours=1),
        submitted_at=now,
        config_snapshot={
            "assembly_mode": assembly,
            "runner_mode": "fixed",
            "assessment_style": "FIXED",
        },
        review_policy=review_policy,
        release_status="published",
    )
    db.add(session)
    db.commit()
    return session


@pytest.mark.parametrize("mutation", ["LEGACY", "ADAPTIVE", "PRACTICE"])
def test_non_eligible_sessions_have_no_review(client, db_session, mutation):
    learner = _make_account(db_session, f"bare-{mutation.lower()}@test.dev", "Learner")
    if mutation == "LEGACY":
        session = _bare_session(db_session, learner)
    elif mutation == "ADAPTIVE":
        session = _bare_session(db_session, learner, review_policy="AI_OFFICIAL_REVIEW",
                                assembly="ADAPTIVE")
    else:
        session = _bare_session(db_session, learner, purpose="PRACTICE")
    response = _request(client, learner, session.session_id)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "review_not_eligible"


def test_finalize_failure_rolls_back_and_allows_resubmit(client, db_session, monkeypatch):
    from app.services import result_version

    _, learner, concepts = fixture(db_session)
    state = _start(client, db_session, learner, concepts)
    sid = state["session_id"]
    auth = headers(learner)
    for attempt in db_session.scalars(select(Attempt).where(Attempt.session_id == sid)):
        saved = _save(client, sid, auth, attempt.seq_no, 1,
                      _answer(attempt.question_snapshot, correct=True))
        assert saved.status_code == 200
    original = result_version.ensure_official_v1

    def boom(db, session):
        raise RuntimeError("injected finalize failure")

    monkeypatch.setattr(result_version, "ensure_official_v1", boom)
    failing = TestClient(app, raise_server_exceptions=False)
    first = failing.post(SUBMIT.format(sid=sid), headers=auth, json={})
    assert first.status_code == 500
    db_session.expire_all()
    assert db_session.get(AssessmentSession, sid).status == "in_progress"
    monkeypatch.setattr(result_version, "ensure_official_v1", original)
    second = client.post(SUBMIT.format(sid=sid), headers=auth, json={})
    assert second.status_code == 200, second.text
    assert second.json()["result_version"] == 1
    assert second.json()["can_request_review"] is True
