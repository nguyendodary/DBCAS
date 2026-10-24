"""Focused supervisor gates: ordinary authoring and safe exam navigation."""
from datetime import timedelta
from decimal import Decimal

import pytest

from app.models import AssessmentSession, Question
from test_adaptive_engine import _make_account
from test_draft_lifecycle import _fixture
from test_supervisor_requirements import headers, started
from test_supervisor_requirements import bank, selection


@pytest.mark.parametrize("code", [None, "", "   "])
def test_concept_reference_is_optional_unique_and_keeps_metadata(client, db_session, code):
    admin = _make_account(db_session, "metadata-admin@test.dev", "Administrator")
    payload = {"concept_name": "Phép nối SQL", "subject_area": "SQL",
               "description": "Combine related rows", "keywords": [" join ", "join"],
               "learning_objectives": ["Compare inner and outer joins"], "sql_feature": "join"}
    if code is not None:
        payload["concept_code"] = code
    results = [client.post("/api/v1/admin/concepts", headers=headers(admin, "Administrator"), json=payload)
               for _ in range(2)]
    assert [r.status_code for r in results] == [201, 201]
    first, second = [r.json() for r in results]
    assert first["concept_code"] != second["concept_code"]
    assert 1 <= len(first["concept_code"]) <= 30
    assert first["concept_name"] == payload["concept_name"]
    assert first["keywords"] == ["join"]
    assert first["learning_objectives"] == payload["learning_objectives"]
    assert first["sql_feature"] == "join"
    denied = client.post("/api/v1/admin/concepts", json=payload)
    assert denied.status_code == 401


@pytest.mark.parametrize("field", ["concept_name", "subject_area"])
def test_blank_concept_classification_is_rejected(client, db_session, field):
    admin = _make_account(db_session, "metadata-admin@test.dev", "Administrator")
    response = client.post("/api/v1/admin/concepts", headers=headers(admin, "Administrator"),
        json={"concept_name": "Joins", "subject_area": "SQL", field: "   "})
    assert response.status_code == 422


@pytest.mark.parametrize("problem,expected", [
    ("prompt", "non-empty question content"),
    ("option", "non-empty option text"),
    ("duplicate", "distinct answer options for human review"),
])
def test_incomplete_or_ambiguous_mcq_cannot_be_approved(client, db_session, problem, expected):
    _, _, _, question, _, _, _ = _fixture(db_session)
    admin = _make_account(db_session, "quality-admin@test.dev", "Administrator")
    question.status = "draft"
    if problem == "prompt":
        question.prompt = "   "
    elif problem == "option":
        question.options[0].option_text = "   "
    else:
        question.options[1].option_text = question.options[0].option_text
    db_session.commit()
    response = client.patch(f"/api/v1/admin/questions/{question.question_id}",
        headers=headers(admin, "Administrator"), json={"status": "validated"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "question_incomplete"
    assert {"missing": expected} in response.json()["error"]["details"]
    db_session.refresh(question)
    assert question.status == "draft"


def test_case_distinct_sql_identifiers_remain_valid_mcq_choices(client, db_session):
    _, _, _, question, _, _, _ = _fixture(db_session)
    admin = _make_account(db_session, "quality-admin@test.dev", "Administrator")
    question.status = "draft"
    question.prompt = 'Which query references the mixed-case "EmployeeID" column?'
    question.options[0].option_text = 'SELECT "EmployeeID" FROM employee;'
    question.options[1].option_text = 'SELECT "employeeid" FROM employee;'
    db_session.commit()
    response = client.patch(f"/api/v1/admin/questions/{question.question_id}",
        headers=headers(admin, "Administrator"), json={"status": "validated"})
    assert response.status_code == 200
    assert {o["option_text"] for o in response.json()["options"]} == {
        'SELECT "EmployeeID" FROM employee;', 'SELECT "employeeid" FROM employee;'}


@pytest.mark.parametrize("kind", ["mcq", "sql", "essay"])
def test_delivered_question_browsing_keeps_own_answers_and_hides_grading(client, db_session, kind):
    learner, session, attempt, question, _, auth, answer = _fixture(db_session, kind, policy="HUMAN_VERIFIED")
    # Store a delivered immutable snapshot just as the actual serve path does.
    from app.repositories import AssessmentRepository
    from app.services.evidence_context import capture_question
    attempt.question_snapshot = capture_question(AssessmentRepository(db_session), question)
    attempt.submitted_at = AssessmentRepository(db_session).server_time()
    attempt.score = Decimal("1")
    attempt.grading_status = "graded"
    for field, value in answer.items():
        setattr(attempt, field, value)
    session.release_status = "unsubmitted"
    before_expiry = session.expires_at
    db_session.commit()
    url = f"/api/v1/sessions/{session.session_id}/questions"
    response = client.get(url, headers=auth)
    assert response.status_code == 200
    item, = response.json()
    assert item["question_id"] == question.question_id
    assert item["submitted_at"] and item["score"] is None
    for field, value in answer.items():
        assert item[field] == value
    forbidden = {"reference_answer", "is_correct", "expected_result", "grading_detail", "rubrics", "question_snapshot"}
    def keys(value):
        if isinstance(value, dict):
            return set(value) | set().union(*(keys(v) for v in value.values()))
        if isinstance(value, list):
            return set().union(*(keys(v) for v in value))
        return set()
    assert not forbidden & keys(item)
    db_session.refresh(session)
    assert session.expires_at == before_expiry and session.status == "in_progress"
    other = _make_account(db_session, "other-learner@test.dev", "Learner")
    admin = _make_account(db_session, "other-admin@test.dev", "Administrator")
    assert client.get(url, headers=headers(other)).status_code == 404
    assert client.get(url, headers=headers(admin, "Administrator")).status_code == 403
    assert client.get(url).status_code == 401
    # Browsing never unlocks submitted answers for editing.
    assert client.put(f"/api/v1/sessions/{session.session_id}/draft", headers=auth,
        json={"question_id": question.question_id, "revision": 1, **answer}).status_code == 409


def test_browsing_excludes_future_plan_and_keeps_frozen_question_content(client, db_session):
    _, learner, _, _, state, _ = started(client, db_session, difficulty=3)
    session = db_session.get(AssessmentSession, state["session_id"])
    delivered = state["current_question"]
    question = db_session.get(Question, delivered["question_id"])
    question.prompt = "Bank content edited after delivery"
    db_session.commit()
    url = f"/api/v1/sessions/{session.session_id}/questions"
    response = client.get(url, headers=headers(learner))
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["prompt"] == delivered["prompt"]
    future = set(session.config_snapshot["question_ids"]) - {delivered["question_id"]}
    assert not future & {q["question_id"] for q in response.json()}


def test_browsing_expired_or_finalized_sessions_does_not_bypass_release(client, db_session):
    _, session, _, _, _, auth, _ = _fixture(db_session, policy="HUMAN_VERIFIED")
    session.expires_at -= timedelta(hours=2)
    db_session.commit()
    response = client.get(f"/api/v1/sessions/{session.session_id}/questions", headers=auth)
    assert response.status_code == 409
    assert client.get(f"/api/v1/sessions/{session.session_id}/evidence", headers=auth).status_code == 409


@pytest.mark.parametrize("inventory,expected", [(0, 0), (1, 1), (2, 2), (6, 3)])
def test_automatic_practice_fits_inventory_without_skill_or_difficulty_substitution(client, db_session, inventory, expected):
    _, learner, concepts, assessment = bank(db_session, difficulty=3, skills=1)
    questions = db_session.query(Question).order_by(Question.question_id).all()
    for i, question in enumerate(questions):
        question.status = "validated" if i < inventory else "draft"
    db_session.commit()
    payload = {**selection(concepts, "MEDIUM"), "mode": "PRACTICE", "question_count": None}
    url = f"/api/v1/assessments/{assessment.assessment_id}/sessions"
    result = client.post(url, headers=headers(learner), json=payload)
    if not inventory:
        assert result.status_code == 422 and result.json()["error"]["code"] == "insufficient_question_pool"
        assert not db_session.query(AssessmentSession).count()
        return
    assert result.status_code == 201, result.json()
    session = db_session.get(AssessmentSession, result.json()["session_id"])
    assert result.json()["max_questions"] == expected
    assert len(session.config_snapshot["question_plan"]) == expected
    assert {q["difficulty_level"] for q in session.config_snapshot["question_plan"]} == {3}
    assert {c["concept_id"] for q in session.config_snapshot["question_plan"] for c in q["concepts"]} == {concepts[0].concept_id}
    assert client.post(url, headers=headers(learner), json=payload).json()["session_id"] == session.session_id
    explicit = {**payload, "question_count": 3}
    assert client.post(url, headers=headers(learner), json=explicit).status_code == 409
