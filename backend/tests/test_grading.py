"""Rule-based MCQ scoring tests — Task 2.3.

Attempts are created directly via ORM (as the serving/adaptive flow would);
the endpoint then grades the pending attempt.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models import (
    Account,
    AccountRole,
    Assessment,
    AssessmentSession,
    Attempt,
    McqOption,
    Question,
    Role,
    UserProfile,
)
from app.security import hash_password
from app.services.grading_service import score_mcq


@pytest.fixture()
def learner_token(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Learner One",
            "email": "learner@test.dev",
            "password": "Secret123!",
            "password_confirm": "Secret123!",
        },
    )
    return client.post(
        "/api/v1/auth/login",
        json={"email": "learner@test.dev", "password": "Secret123!"},
    ).json()["access_token"]


def _learner_account(db):
    return db.query(Account).filter_by(email="learner@test.dev").one()


@pytest.fixture()
def served_mcq(db_session, learner_token):
    """A live session with one served MCQ attempt awaiting an answer."""
    learner = _learner_account(db_session)
    assessment = Assessment(title="A1", status="active", created_by=learner.account_id)
    question = Question(
        question_type="mcq",
        prompt="Which key uniquely identifies a row?",
        question_id=None,
        difficulty_level=1,
        points=Decimal("2.0"),
        status="validated",
        created_by=learner.account_id,
    )
    question.options = [
        McqOption(option_label="A", option_text="Foreign key", is_correct=False),
        McqOption(option_label="B", option_text="Primary key", is_correct=True),
        McqOption(option_label="C", option_text="Index", is_correct=False),
    ]
    session = AssessmentSession(
        assessment=assessment,
        learner_id=learner.account_id,
        status="in_progress",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
    )
    attempt = Attempt(session=session, question=question, seq_no=1)
    db_session.add_all([question, session])
    db_session.commit()
    return {
        "token": learner_token,
        "session_id": session.session_id,
        "question_id": question.question_id,
        "correct_option_id": next(o.option_id for o in question.options if o.is_correct),
        "wrong_option_id": next(o.option_id for o in question.options if not o.is_correct),
    }


def _submit(client, served, option_id=None, question_id=None):
    payload = {"question_id": question_id or served["question_id"]}
    if option_id != "OMIT":
        payload["selected_option_id"] = option_id
    return client.post(
        f"/api/v1/sessions/{served['session_id']}/answers",
        headers={"Authorization": f"Bearer {served['token']}"},
        json=payload,
    )


def test_correct_answer_full_points(client, served_mcq):
    r = _submit(client, served_mcq, served_mcq["correct_option_id"])
    assert r.status_code == 200
    body = r.json()
    assert body["is_correct"] is True
    assert float(body["score"]) == 2.0
    assert float(body["points_possible"]) == 2.0
    assert "correct_option_id" not in body  # answer key not exposed


def test_wrong_answer_zero(client, served_mcq):
    r = _submit(client, served_mcq, served_mcq["wrong_option_id"])
    assert r.status_code == 200
    body = r.json()
    assert body["is_correct"] is False
    assert float(body["score"]) == 0.0


def test_unanswered_scores_zero(client, served_mcq):
    r = _submit(client, served_mcq, None)
    assert r.status_code == 200
    assert float(r.json()["score"]) == 0.0


def test_omitted_option_scores_zero(client, served_mcq):
    r = _submit(client, served_mcq, "OMIT")
    assert r.status_code == 200
    assert float(r.json()["score"]) == 0.0


def test_invalid_option(client, served_mcq):
    r = _submit(client, served_mcq, 999999)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_option"


def test_option_from_other_question_rejected(client, served_mcq, db_session):
    other = Question(
        question_type="mcq", prompt="Other", points=Decimal("1.0"),
        status="validated", created_by=_learner_account(db_session).account_id,
    )
    other.options = [McqOption(option_label="A", option_text="x", is_correct=True)]
    db_session.add(other)
    db_session.commit()
    r = _submit(client, served_mcq, other.options[0].option_id)
    assert r.status_code == 422


def test_duplicate_submission_rejected(client, served_mcq):
    assert _submit(client, served_mcq, served_mcq["correct_option_id"]).status_code == 200
    r = _submit(client, served_mcq, served_mcq["wrong_option_id"])
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "already_submitted"


def test_question_not_served(client, served_mcq):
    r = _submit(client, served_mcq, served_mcq["correct_option_id"], question_id=999999)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "question_not_served"


def test_session_not_found(client, served_mcq):
    r = client.post(
        "/api/v1/sessions/999999/answers",
        headers={"Authorization": f"Bearer {served_mcq['token']}"},
        json={"question_id": served_mcq["question_id"]},
    )
    assert r.status_code == 404


def test_other_learners_session_forbidden(client, served_mcq, db_session):
    other = Account(
        email="other@test.dev", password_hash=hash_password("Secret123!"), status="active"
    )
    other.profile = UserProfile(full_name="Other")
    role = db_session.query(Role).filter_by(role_name="Learner").one()
    db_session.add(other)
    db_session.flush()
    db_session.add(AccountRole(account_id=other.account_id, role_id=role.role_id))
    db_session.commit()
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "other@test.dev", "password": "Secret123!"},
    ).json()["access_token"]
    served = dict(served_mcq, token=token)
    r = _submit(client, served, served_mcq["correct_option_id"])
    assert r.status_code == 404  # not theirs — do not reveal existence


def test_admin_cannot_submit_answers(client, served_mcq, db_session):
    admin = Account(
        email="admin@test.dev", password_hash=hash_password("Admin123!"), status="active"
    )
    admin.profile = UserProfile(full_name="A")
    role = db_session.query(Role).filter_by(role_name="Administrator").one()
    db_session.add(admin)
    db_session.flush()
    db_session.add(AccountRole(account_id=admin.account_id, role_id=role.role_id))
    db_session.commit()
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.dev", "password": "Admin123!"},
    ).json()["access_token"]
    served = dict(served_mcq, token=token)
    r = _submit(client, served, served_mcq["correct_option_id"])
    assert r.status_code == 403


def test_expired_session_rejected(client, served_mcq, db_session):
    session = db_session.get(AssessmentSession, served_mcq["session_id"])
    session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()
    r = _submit(client, served_mcq, served_mcq["correct_option_id"])
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "session_expired"
    db_session.refresh(session)
    assert session.status == "timed_out"


def test_non_mcq_attempt_rejected(client, served_mcq, db_session):
    # Essay grading arrives with Task 3.5 — until then it stays unsupported.
    learner = _learner_account(db_session)
    essay_q = Question(
        question_type="essay", prompt="Explain normalization",
        points=Decimal("3.0"), status="validated", created_by=learner.account_id,
    )
    attempt = Attempt(
        session_id=served_mcq["session_id"], question=essay_q, seq_no=2
    )
    db_session.add_all([essay_q, attempt])
    db_session.commit()
    r = _submit(client, served_mcq, None, question_id=essay_q.question_id)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unsupported_question_type"


def test_unauthenticated_submit(client, served_mcq):
    r = client.post(
        f"/api/v1/sessions/{served_mcq['session_id']}/answers",
        json={"question_id": served_mcq["question_id"]},
    )
    assert r.status_code == 401


def test_grading_detail_stored(client, served_mcq, db_session):
    _submit(client, served_mcq, served_mcq["correct_option_id"])
    attempt = (
        db_session.query(Attempt)
        .filter_by(session_id=served_mcq["session_id"])
        .one()
    )
    assert attempt.submitted_at is not None
    assert float(attempt.score) == 2.0
    assert attempt.grading_detail["grader"] == "answer_key"
    assert attempt.grading_detail["is_correct"] is True


# ---------- pure scoring-rule unit tests ----------

class _Opt:
    def __init__(self, oid, correct):
        self.option_id = oid
        self.is_correct = correct


class _Q:
    def __init__(self, points):
        self.points = Decimal(str(points))


def test_score_mcq_correct():
    opts = [_Opt(1, False), _Opt(2, True)]
    r = score_mcq(_Q(2.5), opts, 2)
    assert r["is_correct"] is True and float(r["score"]) == 2.5


def test_score_mcq_wrong():
    opts = [_Opt(1, False), _Opt(2, True)]
    r = score_mcq(_Q(2.5), opts, 1)
    assert r["is_correct"] is False and float(r["score"]) == 0


def test_score_mcq_unanswered():
    r = score_mcq(_Q(1), [_Opt(1, True)], None)
    assert r["is_correct"] is False and float(r["score"]) == 0


def test_score_mcq_bad_option():
    with pytest.raises(Exception) as e:
        score_mcq(_Q(1), [_Opt(1, True)], 99)
    assert getattr(e.value, "status_code", None) == 422
