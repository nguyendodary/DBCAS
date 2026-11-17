"""FIXED-paper tab-leave anti-cheat: server-timed, idempotent, final."""
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import func, select

from app.models import Attempt, AssessmentSession, TabLeaveInterval
from test_admin_analytics import _make_account
from test_learner_practice import _fixed_payload, fixture, selection
from test_supervisor_requirements import headers


def _start(client, learner, concepts):
    response = client.post('/api/v1/practice/start', headers=headers(learner),
                           json=_fixed_payload(concepts))
    assert response.status_code == 200, response.text
    return response.json()["session_id"]


def _report(client, sid, auth, event, *, event_id=None, leave_id=None):
    body = {"event": event, "event_id": str(event_id or uuid4())}
    if leave_id:
        body["leave_event_id"] = str(leave_id)
    return client.post(f"/api/v1/sessions/{sid}/paper/tab-leave",
                       headers=auth, json=body)


def _leave(client, sid, auth):
    event_id = uuid4()
    response = _report(client, sid, auth, "leave", event_id=event_id)
    assert response.status_code == 200, response.text
    return event_id, response.json()


def _shift_away(db, sid, seconds=5):
    db.expire_all()
    interval = db.scalar(select(TabLeaveInterval).where(
        TabLeaveInterval.session_id == sid,
        TabLeaveInterval.returned_at.is_(None)))
    assert interval is not None
    interval.left_at = interval.left_at - timedelta(seconds=seconds)
    db.commit()


def _return(client, sid, auth, leave_id=None, event_id=None):
    response = _report(client, sid, auth, "return", event_id=event_id,
                       leave_id=leave_id)
    assert response.status_code == 200, response.text
    return response.json()


def test_short_absence_never_counts_and_reload_keeps_the_counter(client, db_session):
    _, learner, concepts = fixture(db_session)
    sid = _start(client, learner, concepts)
    auth = headers(learner)

    leave_id, _ = _leave(client, sid, auth)
    assert _return(client, sid, auth, leave_id)["violation_count"] == 0
    db_session.expire_all()
    assert db_session.get(AssessmentSession, sid).tab_leave_count == 0

    leave_id, _ = _leave(client, sid, auth)
    _shift_away(db_session, sid)
    state = _return(client, sid, auth, leave_id)
    assert state["counted"] is True and state["violation_count"] == 1
    assert state["warning_level"] == 1 and state["cancelled"] is False

    # Reload/re-entry reads the persisted count, not a client-side tally.
    meta = client.get(f"/api/v1/sessions/{sid}/paper", headers=auth).json()
    assert meta["tab_leave_count"] == 1
    assert meta["tab_leave_grace_seconds"] == 3
    assert meta["tab_leave_violation_limit"] == 3


def test_event_retries_are_idempotent_and_orphan_returns_are_ignored(client, db_session):
    _, learner, concepts = fixture(db_session)
    sid = _start(client, learner, concepts)
    auth = headers(learner)

    orphan = _return(client, sid, auth)
    assert orphan["violation_count"] == 0

    leave_id, _ = _leave(client, sid, auth)
    _report(client, sid, auth, "leave", event_id=leave_id)
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(TabLeaveInterval).where(
        TabLeaveInterval.session_id == sid)) == 1

    _shift_away(db_session, sid)
    event_id = uuid4()
    first = _return(client, sid, auth, leave_id, event_id)
    assert first["violation_count"] == 1
    retry = _return(client, sid, auth, leave_id, event_id)
    assert retry["violation_count"] == 1 and retry["counted"] is False
    db_session.expire_all()
    assert db_session.get(AssessmentSession, sid).tab_leave_count == 1


def test_third_violation_cancels_with_zero_points_and_is_final(client, db_session):
    _, learner, concepts = fixture(db_session)
    sid = _start(client, learner, concepts)
    auth = headers(learner)

    for expected in (1, 2):
        leave_id, _ = _leave(client, sid, auth)
        _shift_away(db_session, sid)
        state = _return(client, sid, auth, leave_id)
        assert state["violation_count"] == expected
        assert state["warning_level"] == expected
        assert state["cancelled"] is False

    leave_id, _ = _leave(client, sid, auth)
    _shift_away(db_session, sid)
    cancelled = _return(client, sid, auth, leave_id)
    assert cancelled["cancelled"] is True and cancelled["violation_count"] == 3
    assert cancelled["cancel_reason"] == "tab_leave_limit"
    cancelled_at = cancelled["server_now"]
    assert cancelled_at

    # Duplicate report and final submit are idempotent: no extra cancellation.
    assert _return(client, sid, auth, leave_id)["violation_count"] == 3
    first = client.post(f"/api/v1/sessions/{sid}/paper/submit", headers=auth, json={})
    second = client.post(f"/api/v1/sessions/{sid}/paper/submit", headers=auth, json={})
    assert first.status_code == 200 and second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["status"] == "cancelled"
    assert first.json()["cancelled"] is True
    assert first.json()["cancel_reason"] == "tab_leave_limit"

    db_session.expire_all()
    session = db_session.get(AssessmentSession, sid)
    assert session.status == "cancelled" and session.cancelled_at is not None
    attempts = list(db_session.scalars(select(Attempt).where(Attempt.session_id == sid)))
    assert attempts and all(a.score == 0 and a.grading_status == "graded"
                            and a.submitted_at is not None for a in attempts)

    # Cancelled papers are final: no late draft can change the result.
    late = client.put(f"/api/v1/sessions/{sid}/paper/1/draft", headers=auth,
                      json={"revision": 1, "selected_option_id": 1})
    assert late.status_code == 409
    assert late.json()["error"]["code"] == "session_not_active"
    assert client.get(f"/api/v1/sessions/{sid}/paper", headers=auth).status_code == 409

    history = client.get("/api/v1/sessions", headers=auth).json()
    summary = next(item for item in history if item["session_id"] == sid)
    assert summary["status"] == "cancelled"
    assert summary["tab_leave_count"] == 3
    assert summary["cancel_reason"] == "tab_leave_limit"
    assert summary["overall_result_pct"] in ("0", "0.00")

    result = client.get(f"/api/v1/evaluations/attempts/{sid}", headers=auth).json()
    assert result["status"] == "cancelled"
    assert result["score"]["percentage"] == 0
    assert result["cancel_reason"] == "tab_leave_limit"


def test_admin_sees_violation_count_and_cancellation_reason(client, db_session):
    _, learner, concepts = fixture(db_session)
    sid = _start(client, learner, concepts)
    auth = headers(learner)
    for _ in range(3):
        leave_id, _ = _leave(client, sid, auth)
        _shift_away(db_session, sid)
        _return(client, sid, auth, leave_id)

    admin = _make_account(db_session, "tab-admin@test", "Administrator", "Tab Admin")
    response = client.get(f"/api/v1/admin/learners/{learner.account_id}/sessions",
                          headers=headers(admin, role="Administrator"))
    assert response.status_code == 200, response.text
    summary = next(item for item in response.json()["sessions"]
                   if item["session_id"] == sid)
    assert summary["status"] == "cancelled"
    assert summary["tab_leave_count"] == 3
    assert summary["cancel_reason"] == "tab_leave_limit"


def test_tab_leave_reporting_is_fixed_only_and_owner_scoped(client, db_session):
    _, learner, concepts = fixture(db_session)
    legacy = client.post('/api/v1/practice/start', headers=headers(learner),
                         json=selection(concepts)).json()
    response = _report(client, legacy["session_id"], headers(learner), "leave")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "paper_mode_unavailable"

    fixed_learner = _make_account(db_session, "tab-fixed@test", "Learner")
    sid = _start(client, fixed_learner, concepts)
    other = _make_account(db_session, "tab-other@test", "Learner")
    assert _report(client, sid, headers(other), "leave").status_code == 404
