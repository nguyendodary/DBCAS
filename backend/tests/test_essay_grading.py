"""Four-level rubric essay scoring tests — Task 3.5 (DBCAS-20).

The provider is stubbed at the ``LLMService.generate_structured`` boundary:
no HTTP, no real key. Covers every rubric level, clamping, malformed/invalid
responses, missing rubric, provider failure, PII sanitization of the prompt,
and attempt persistence — all per the completion gate.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.deps import get_llm_service
from app.main import app
from app.models import (
    Account,
    Assessment,
    AssessmentSession,
    Attempt,
    Question,
    Rubric,
)
from app.services.essay_grading import _validate_result, grade_essay
from app.services.llm import LLMError


class StubLLM:
    """Returns a canned grading dict; records the prompts it was given."""

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []  # (task_type, messages, json_schema)

    def generate_structured(self, task_type, messages, *, json_schema=None, max_tokens=None):
        self.calls.append(
            {
                "task_type": task_type,
                "messages": list(messages),
                "json_schema": json_schema,
            }
        )
        if self.error is not None:
            raise self.error
        return self.response


def _grade(level_name, score, points="10.0", rubrics=None, extra=None):
    """Validate a provider payload directly (unit level)."""
    rubrics = rubrics if rubrics is not None else _rubrics_model()
    q = Question(
        question_type="essay", prompt="Explain 3NF",
        points=Decimal(points),
    )
    payload = {
        "rubric_level": level_name,
        "score": score,
        "confidence": 0.8,
        "matched_criteria": ["c1"],
        "missing_concepts": [],
        "evidence": ["..."],
        "explanation": "why",
        "feedback": "do better",
    }
    if extra:
        payload.update(extra)
    return _validate_result(payload, q, rubrics)


def _rubrics_model():
    """In-memory rubric rows matching the documented four levels."""
    return [
        Rubric(level_name="Incomplete", min_score=Decimal("0"),
               max_score=Decimal("1"), criteria="Missing or wrong"),
        Rubric(level_name="Partial", min_score=Decimal("2"),
               max_score=Decimal("4"), criteria="Some correct ideas"),
        Rubric(level_name="Mostly Complete", min_score=Decimal("5"),
               max_score=Decimal("7"), criteria="Mostly correct"),
        Rubric(level_name="Complete", min_score=Decimal("8"),
               max_score=Decimal("10"), criteria="Fully correct"),
    ]


class TestResultValidation:
    """_validate_result: level mapping, clamping, rejection — no I/O."""

    @pytest.mark.parametrize(
        "level,score,expected",
        [
            ("Complete", 10, Decimal("10")),
            ("Mostly Complete", 6, Decimal("6")),
            ("Partial", 3, Decimal("3")),
            ("Incomplete", 0, Decimal("0")),
        ],
    )
    def test_levels_map(self, level, score, expected):
        r = _grade(level, score)
        assert r["score"] == expected
        assert r["grading_detail"]["rubric_level"] == level

    def test_level_case_insensitive(self):
        r = _grade("complete", 9)
        assert r["grading_detail"]["rubric_level"] == "Complete"

    def test_score_clamped_to_band(self):
        r = _grade("Partial", 9)  # Partial band tops at 4
        assert r["score"] == Decimal("4")

    def test_score_clamped_to_zero(self):
        r = _grade("Incomplete", -5)
        assert r["score"] == Decimal("0")

    def test_invalid_level_rejected(self):
        with pytest.raises(LLMError) as exc:
            _grade("Excellent", 9)
        assert exc.value.code == LLMError.INVALID_RESPONSE

    def test_non_numeric_score_rejected(self):
        with pytest.raises(LLMError) as exc:
            _grade("Complete", "nine")
        assert exc.value.code == LLMError.INVALID_RESPONSE

    def test_missing_level_rejected(self):
        with pytest.raises(LLMError):
            _grade(None, 5, extra={"rubric_level": None})

    def test_confidence_clamped(self):
        r = _grade("Complete", 9, extra={"confidence": 5})
        assert r["grading_detail"]["confidence"] == "1"

    def test_optional_lists_default_empty(self):
        r = _grade("Complete", 9, extra={"matched_criteria": "nope"})
        assert r["grading_detail"]["matched_criteria"] == []


# ---------- endpoint-level with stubbed LLM dep ----------


def _learner_token(client, email="essay@test.dev"):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Essay Learner",
            "email": email,
            "password": "Secret123!",
            "password_confirm": "Secret123!",
        },
    )
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Secret123!"},
    ).json()["access_token"]


@pytest.fixture()
def served_essay(db_session, client):
    token = _learner_token(client)
    learner = db_session.query(Account).filter_by(email="essay@test.dev").one()
    assessment = Assessment(
        title="Essay A", status="active", created_by=learner.account_id
    )
    question = Question(
        question_type="essay",
        prompt="Explain why 3NF removes transitive dependency",
        reference_answer="3NF removes transitive dependency because ...",
        difficulty_level=3,
        points=Decimal("10.0"),
        status="validated",
        created_by=learner.account_id,
    )
    session = AssessmentSession(
        assessment=assessment,
        learner_id=learner.account_id,
        status="in_progress",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
    )
    attempt = Attempt(session=session, question=question, seq_no=1)
    db_session.add(attempt)
    db_session.flush()
    db_session.add_all(
        [
            Rubric(
                question_id=question.question_id, level_name="Incomplete",
                min_score=Decimal("0"), max_score=Decimal("1"),
                criteria="Missing or fundamentally wrong",
            ),
            Rubric(
                question_id=question.question_id, level_name="Partial",
                min_score=Decimal("2"), max_score=Decimal("4"),
                criteria="Some correct concepts, major gaps",
            ),
            Rubric(
                question_id=question.question_id, level_name="Mostly Complete",
                min_score=Decimal("5"), max_score=Decimal("7"),
                criteria="Mostly correct, minor omissions",
            ),
            Rubric(
                question_id=question.question_id, level_name="Complete",
                min_score=Decimal("8"), max_score=Decimal("10"),
                criteria="Fully correct with reasoning",
            ),
        ]
    )
    db_session.commit()
    return {
        "token": token,
        "session_id": session.session_id,
        "question_id": question.question_id,
        "attempt_id": attempt.attempt_id,
        "learner_id": learner.account_id,
    }


@pytest.fixture()
def stub_llm(client):
    """Overrides the LLM dependency; returns the stub for test control."""
    stub = StubLLM(
        {
            "rubric_level": "Complete",
            "score": 9,
            "confidence": 0.9,
            "matched_criteria": ["mentions transitive dependency"],
            "missing_concepts": [],
            "evidence": ["because non-key attrs depend on other non-keys"],
            "explanation": "Covers the definition fully.",
            "feedback": "Good answer.",
        }
    )
    app.dependency_overrides[get_llm_service] = lambda: stub
    yield stub
    app.dependency_overrides.pop(get_llm_service, None)


def _submit(client, served, essay):
    payload = {"question_id": served["question_id"]}
    if essay is not None:
        payload["essay_answer"] = essay
    return client.post(
        f"/api/v1/sessions/{served['session_id']}/answers",
        headers={"Authorization": f"Bearer {served['token']}"},
        json=payload,
    )


class TestEndpoint:
    def test_complete_answer(self, client, served_essay, stub_llm):
        r = _submit(client, served_essay, "3NF removes transitive dependency because non-key attributes must depend only on the key.")
        assert r.status_code == 200
        body = r.json()
        assert Decimal(body["score"]) == Decimal("9")
        assert body["is_correct"] is True
        # provider was actually invoked with a strict schema
        assert stub_llm.calls[0]["task_type"] == "essay_grading"
        assert stub_llm.calls[0]["json_schema"]["name"] == "essay_grade"

    def test_partial_level(self, client, served_essay, stub_llm, db_session):
        stub_llm.response["rubric_level"] = "Partial"
        stub_llm.response["score"] = 3
        r = _submit(client, served_essay, "It helps normalize tables a bit.")
        assert r.status_code == 200
        attempt = db_session.query(Attempt).filter_by(
            attempt_id=served_essay["attempt_id"]
        ).one()
        assert attempt.score == Decimal("3")
        assert attempt.grading_detail["rubric_level"] == "Partial"
        assert attempt.grading_detail["level_band"] == ["2.00", "4.00"]

    def test_evidence_persisted(self, client, served_essay, stub_llm, db_session):
        text = "3NF removes transitive dependency because non-key attributes depend only on the key."
        _submit(client, served_essay, text)
        attempt = db_session.query(Attempt).filter_by(
            attempt_id=served_essay["attempt_id"]
        ).one()
        detail = attempt.grading_detail
        assert detail["grader"] == "llm_rubric"
        assert detail["matched_criteria"]
        assert detail["evidence"]
        assert detail["feedback"]
        assert detail["points_possible"] == "10.00"
        assert detail["points_earned"] == "9"
        assert attempt.essay_answer == text  # raw stored internally
        assert attempt.submitted_at is not None

    def test_prompt_sanitized(self, client, served_essay, stub_llm):
        _submit(
            client,
            served_essay,
            "I am Essay Learner, student id 20217777. 3NF removes "
            "transitive dependency.",
        )
        sent = stub_llm.calls[0]["messages"][1].content
        assert "Essay Learner" not in sent
        assert "20217777" not in sent
        assert "[name]" in sent and "[id]" in sent

    def test_malformed_llm_response(self, client, served_essay, stub_llm):
        stub_llm.response = {"unexpected": True}  # missing required fields
        r = _submit(client, served_essay, "An answer about 3NF.")
        assert r.status_code == 502
        assert r.json()["error"]["code"] == "llm_invalid_response"

    def test_invalid_rubric_level(self, client, served_essay, stub_llm):
        stub_llm.response["rubric_level"] = "Perfect"
        r = _submit(client, served_essay, "An answer.")
        assert r.status_code == 502

    def test_provider_unavailable(self, client, served_essay, stub_llm):
        stub_llm.error = LLMError(LLMError.UNAVAILABLE, "down")
        r = _submit(client, served_essay, "An answer.")
        assert r.status_code == 503

    def test_not_configured(self, client, served_essay, stub_llm):
        stub_llm.error = LLMError(LLMError.NOT_CONFIGURED, "no key")
        r = _submit(client, served_essay, "An answer.")
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "llm_not_configured"

    def test_empty_answer_rejected(self, client, served_essay, stub_llm):
        assert _submit(client, served_essay, "   ").status_code == 422
        assert _submit(client, served_essay, None).status_code == 422
        assert stub_llm.calls == []  # provider never invoked

    def test_missing_rubric(self, client, served_essay, db_session, stub_llm):
        db_session.query(Rubric).filter_by(
            question_id=served_essay["question_id"]
        ).delete()
        db_session.commit()
        r = _submit(client, served_essay, "An answer.")
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "rubric_not_configured"

    def test_failed_grade_leaves_attempt_pending(
        self, client, served_essay, stub_llm, db_session
    ):
        stub_llm.response = {"bad": "payload"}
        _submit(client, served_essay, "An answer.")
        attempt = db_session.query(Attempt).filter_by(
            attempt_id=served_essay["attempt_id"]
        ).one()
        assert attempt.submitted_at is None  # safe retry remains possible

    def test_double_submit(self, client, served_essay, stub_llm):
        _submit(client, served_essay, "First.")
        r = _submit(client, served_essay, "Second.")
        assert r.status_code == 409


class TestGradeEssayPrompt:
    """grade_essay builds the documented prompt and applies validation."""

    def test_prompt_contains_rubric_and_sanitized_answer(self):
        stub = StubLLM(
            {
                "rubric_level": "Mostly Complete",
                "score": 6,
                "explanation": "x",
            }
        )
        q = Question(
            question_type="essay",
            prompt="Explain 3NF",
            reference_answer="Because ...",
            points=Decimal("10"),
        )
        result = grade_essay(
            q, _rubrics_model(), "Clean answer text.", stub
        )
        assert result["score"] == Decimal("6")
        user_msg = stub.calls[0]["messages"][1].content
        assert "Mostly Complete" in user_msg  # rubric shipped to provider
        assert "Clean answer text." in user_msg
        sys_msg = stub.calls[0]["messages"][0].content
        assert "cite" in sys_msg.lower() and "JSON" in sys_msg
