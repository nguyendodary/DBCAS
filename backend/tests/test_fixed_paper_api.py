"""FIXED paper read/save/flag/final-submit contracts (PR 2).

Legacy sessions keep the per-answer endpoints; these routes only exist for
``config_snapshot.runner_mode == "fixed"`` sessions created by PR 1.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.models import (AssessmentSession, Attempt, EvaluationRecord,
                        GradingJob)
from test_learner_practice import _fixed_payload, complete, fixture, selection
from test_supervisor_requirements import headers


FORBIDDEN = {"score", "is_correct", "grading_status", "grading_detail",
             "reference_answer", "explanation", "expected_result", "rubric",
             "rubrics", "answer_key"}


def _no_keys(value, path="response"):
    """Recursively assert no grade/answer-key field leaked into a paper reply."""
    if isinstance(value, dict):
        for key, nested in value.items():
            assert key not in FORBIDDEN, f"{path}.{key} leaks a key/score"
            _no_keys(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _no_keys(nested, f"{path}[{index}]")


def _start(client, db_session, learner, concepts):
    response = client.post('/api/v1/practice/start', headers=headers(learner),
                           json=_fixed_payload(concepts))
    assert response.status_code == 200, response.text
    return response.json()


def _meta(client, sid, auth):
    response = client.get(f"/api/v1/sessions/{sid}/paper", headers=auth)
    assert response.status_code == 200, response.text
    return response.json()


def _attempt(db_session, sid, seq):
    return db_session.scalar(select(Attempt).where(
        Attempt.session_id == sid, Attempt.seq_no == seq))


def _answer(snapshot, *, correct=False):
    kind = snapshot["question_type"]
    if kind == "mcq":
        options = snapshot["options"]
        option = next((o for o in options if bool(o["is_correct"]) is correct), options[0])
        return {"selected_option_id": option["option_id"]}
    if kind == "sql":
        return {"sql_answer": "SELECT 1"}
    return {"essay_answer": "A complete answer for this question."}


def _seq_of_type(meta, kind):
    return next(q["seq_no"] for q in meta["questions"] if q["question_type"] == kind)


def _save(client, sid, auth, seq, revision, answer):
    return client.put(f"/api/v1/sessions/{sid}/paper/{seq}/draft", headers=auth,
                      json={"revision": revision, **answer})


def test_out_of_order_open_edit_and_return(client, db_session):
    _, learner, concepts = fixture(db_session)
    state = _start(client, db_session, learner, concepts)
    sid = state["session_id"]
    auth = headers(learner)

    meta = _meta(client, sid, auth)
    assert meta["runner_mode"] == "fixed" and meta["status"] == "in_progress"
    assert meta["question_count"] == 3 and meta["answered_count"] == 0
    assert meta["flagged_count"] == 0 and meta["last_opened_seq"] is None
    assert [q["seq_no"] for q in meta["questions"]] == [1, 2, 3]
    assert all(q["opened"] is False and q["answered"] is False for q in meta["questions"])
    _no_keys(meta)

    first_seq, last_seq = 1, 3
    last = client.get(f"/api/v1/sessions/{sid}/paper/{last_seq}", headers=auth)
    assert last.status_code == 200, last.text
    view_last = last.json()
    assert view_last["seq_no"] == last_seq and view_last["first_opened_at"]
    assert view_last["draft"] is None and view_last["answered"] is False
    _no_keys(view_last)
    saved_last = _save(client, sid, auth, last_seq, 1,
                       _answer(_attempt(db_session, sid, last_seq).question_snapshot))
    assert saved_last.status_code == 200, saved_last.text

    client.get(f"/api/v1/sessions/{sid}/paper/{first_seq}", headers=auth)
    assert _save(client, sid, auth, first_seq, 1,
                 _answer(_attempt(db_session, sid, first_seq).question_snapshot)).status_code == 200
    again = client.get(f"/api/v1/sessions/{sid}/paper/{last_seq}", headers=auth).json()
    assert again["answered"] is True and again["draft_revision"] == 1
    assert again["first_opened_at"] == view_last["first_opened_at"]

    meta = _meta(client, sid, auth)
    assert meta["answered_count"] == 2
    # first_opened_at is set once, so resume lands on the most recently opened.
    assert meta["last_opened_seq"] == first_seq
    by_seq = {q["seq_no"]: q for q in meta["questions"]}
    assert by_seq[first_seq]["opened"] and by_seq[first_seq]["answered"]
    assert by_seq[2]["opened"] is False and by_seq[2]["answered"] is False
    assert by_seq[last_seq]["draft_revision"] == 1


def test_flags_and_revision_conflicts(client, db_session):
    _, learner, concepts = fixture(db_session)
    state = _start(client, db_session, learner, concepts)
    sid = state["session_id"]
    auth = headers(learner)
    meta = _meta(client, sid, auth)

    flagged = client.put(f"/api/v1/sessions/{sid}/paper/2/flag", headers=auth,
                         json={"flagged": True, "revision": 0})
    assert flagged.status_code == 200 and flagged.json() == {
        "seq_no": 2, "flagged": True, "revision": 1}
    stale = client.put(f"/api/v1/sessions/{sid}/paper/2/flag", headers=auth,
                       json={"flagged": False, "revision": 0})
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "flag_revision_conflict"
    assert stale.json()["error"]["details"]["revision"] == 1
    cleared = client.put(f"/api/v1/sessions/{sid}/paper/2/flag", headers=auth,
                         json={"flagged": False, "revision": 1})
    assert cleared.status_code == 200 and cleared.json()["revision"] == 2
    assert _meta(client, sid, auth)["flagged_count"] == 0

    mcq_seq = _seq_of_type(meta, "mcq")
    wrong_shape = {"sql_answer": "SELECT 1"}
    mismatch = _save(client, sid, auth, mcq_seq, 1, wrong_shape)
    assert mismatch.status_code == 422
    assert mismatch.json()["error"]["code"] == "answer_type_mismatch"
    snapshot = _attempt(db_session, sid, mcq_seq).question_snapshot
    assert _save(client, sid, auth, mcq_seq, 1,
                 _answer(snapshot, correct=True)).status_code == 200
    conflict = _save(client, sid, auth, mcq_seq, 1, _answer(snapshot, correct=False))
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "draft_revision_conflict"
    assert conflict.json()["error"]["details"]["revision"] == 1
    bad_option = _save(client, sid, auth, mcq_seq, 2, {"selected_option_id": 999999})
    assert bad_option.status_code == 422
    assert bad_option.json()["error"]["code"] == "invalid_option"
    missing = _save(client, sid, auth, 99, 1, {"sql_answer": "x"})
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "question_not_in_paper"


def test_paper_responses_never_expose_keys_or_scores(client, db_session):
    _, learner, concepts = fixture(db_session)
    state = _start(client, db_session, learner, concepts)
    sid = state["session_id"]
    auth = headers(learner)
    meta = _meta(client, sid, auth)
    _no_keys(meta)
    for seq in (1, 2, 3):
        view = client.get(f"/api/v1/sessions/{sid}/paper/{seq}", headers=auth)
        assert view.status_code == 200, view.text
        _no_keys(view.json())
    saved = _save(client, sid, auth, 1, 1,
                  _answer(_attempt(db_session, sid, 1).question_snapshot))
    assert saved.status_code == 200
    _no_keys(saved.json())
    flagged = client.put(f"/api/v1/sessions/{sid}/paper/1/flag", headers=auth,
                         json={"flagged": True, "revision": 0})
    assert flagged.status_code == 200
    _no_keys(flagged.json())
    submitted = client.post(f"/api/v1/sessions/{sid}/paper/submit", headers=auth, json={})
    assert submitted.status_code == 200, submitted.text
    _no_keys(submitted.json())


def test_final_submit_grades_once_and_is_idempotent_across_tabs(client, db_session):
    _, learner, concepts = fixture(db_session)
    state = _start(client, db_session, learner, concepts)
    sid = state["session_id"]
    auth = headers(learner)
    meta = _meta(client, sid, auth)
    mcq_seq = _seq_of_type(meta, "mcq")
    sql_seq = _seq_of_type(meta, "sql")

    assert _save(client, sid, auth, mcq_seq, 1,
                 _answer(_attempt(db_session, sid, mcq_seq).question_snapshot,
                         correct=True)).status_code == 200
    assert _save(client, sid, auth, sql_seq, 1,
                 _answer(_attempt(db_session, sid, sql_seq).question_snapshot)).status_code == 200

    db_session.expire_all()
    before = list(db_session.scalars(select(Attempt).where(Attempt.session_id == sid)))
    assert all(a.submitted_at is None and a.score is None for a in before)
    assert db_session.scalar(select(func.count()).select_from(GradingJob)) == 0
    assert db_session.scalar(select(func.count()).select_from(EvaluationRecord)) == 0

    first = client.post(f"/api/v1/sessions/{sid}/paper/submit", headers=auth,
                        json={"request_id": str(uuid4())})
    assert first.status_code == 200, first.text
    summary = first.json()
    assert summary["status"] == "completed" and summary["final"] is True
    assert summary["answered_count"] == 2 and summary["unanswered_count"] == 1
    assert summary["next"] == f"/evaluations/{sid}" and summary["submitted_at"]

    second = client.post(f"/api/v1/sessions/{sid}/paper/submit", headers=auth,
                         json={"request_id": str(uuid4())})
    assert second.status_code == 200 and second.json() == summary

    db_session.expire_all()
    by_seq = {a.seq_no: a for a in db_session.scalars(
        select(Attempt).where(Attempt.session_id == sid))}
    assert by_seq[mcq_seq].score == 1 and by_seq[mcq_seq].grading_status == "graded"
    assert by_seq[sql_seq].grading_status == "pending"
    unanswered = next(seq for seq in (1, 2, 3) if seq not in (mcq_seq, sql_seq))
    assert by_seq[unanswered].score == 0 and by_seq[unanswered].grading_status == "graded"
    assert db_session.scalar(select(func.count()).select_from(GradingJob).where(
        GradingJob.attempt_id == by_seq[sql_seq].attempt_id)) == 1
    session = db_session.get(AssessmentSession, sid)
    assert session.status == "completed" and session.submitted_at is not None


def test_expiry_finalizes_saved_drafts_and_rejects_late_save(client, db_session):
    _, learner, concepts = fixture(db_session)
    state = _start(client, db_session, learner, concepts)
    sid = state["session_id"]
    auth = headers(learner)
    meta = _meta(client, sid, auth)
    mcq_seq = _seq_of_type(meta, "mcq")
    other_seq = next(seq for seq in (1, 2, 3) if seq != mcq_seq)
    assert _save(client, sid, auth, mcq_seq, 1,
                 _answer(_attempt(db_session, sid, mcq_seq).question_snapshot,
                         correct=True)).status_code == 200

    session = db_session.get(AssessmentSession, sid)
    deadline = datetime.now(timezone.utc) - timedelta(seconds=1)
    session.expires_at = deadline
    db_session.commit()

    late = _save(client, sid, auth, other_seq, 1,
                 _answer(_attempt(db_session, sid, other_seq).question_snapshot))
    assert late.status_code == 409 and late.json()["error"]["code"] == "session_expired"
    meta_response = client.get(f"/api/v1/sessions/{sid}/paper", headers=auth)
    assert meta_response.status_code == 409
    assert meta_response.json()["error"]["code"] == "session_expired"

    db_session.expire_all()
    assert session.status == "timed_out" and session.submitted_at == deadline
    by_seq = {a.seq_no: a for a in db_session.scalars(
        select(Attempt).where(Attempt.session_id == sid))}
    assert by_seq[mcq_seq].score == 1 and by_seq[mcq_seq].submitted_at == deadline
    assert by_seq[other_seq].score == 0 and by_seq[other_seq].submitted_at == deadline

    summary = client.post(f"/api/v1/sessions/{sid}/paper/submit", headers=auth, json={})
    assert summary.status_code == 200 and summary.json()["status"] == "timed_out"


def test_legacy_sessions_are_unaffected(client, db_session):
    _, learner, concepts = fixture(db_session)
    state = client.post('/api/v1/practice/start', headers=headers(learner),
                        json=selection(concepts)).json()
    assert state.get("runner_mode") is None
    sid = state["session_id"]
    auth = headers(learner)

    for method, path, body in (
        ("get", f"/api/v1/sessions/{sid}/paper", None),
        ("get", f"/api/v1/sessions/{sid}/paper/1", None),
        ("put", f"/api/v1/sessions/{sid}/paper/1/draft", {"revision": 1, "sql_answer": "x"}),
        ("put", f"/api/v1/sessions/{sid}/paper/1/flag", {"flagged": True, "revision": 0}),
        ("post", f"/api/v1/sessions/{sid}/paper/submit", {}),
    ):
        if body is None:
            response = getattr(client, method)(path, headers=auth)
        else:
            response = getattr(client, method)(path, headers=auth, json=body)
        assert response.status_code == 409, (path, response.text)
        assert response.json()["error"]["code"] == "paper_mode_unavailable"

    finished = complete(client, db_session, learner, state)
    assert finished["status"] == "completed"
