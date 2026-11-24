"""Mode 2 live generation against the real PostgreSQL test fixtures."""
import re
from uuid import uuid4

from sqlalchemy import select

from app.models import AssessmentSession, Attempt
from app.schemas import SubmitAnswerRequest
from app.services import adaptive_engine, assessment_lifecycle, practice_service as practice
from test_learner_practice import fixture


class FakeLLM:
    def __init__(self, concept_id, *, fail=False):
        self.concept_id = concept_id
        self.fail = fail
        self.calls = 0

    def is_configured(self):
        return True

    def with_budget(self, **_):
        return self

    def generate_structured(self, _task, messages, **_):
        self.calls += 1
        if self.fail:
            raise TimeoutError("provider timeout")
        prompt = messages[0].content
        level = int(re.search(r"Difficulty level: (\d+)", prompt).group(1))
        item = {
            "concept_ids": [self.concept_id],
            "difficulty_level": level,
            "question_type": "mcq",
            "prompt": f"AI generated MCQ {self.calls} for concept {self.concept_id} level {level}.",
            "explanation": "A deterministic generated explanation for this practice question.",
            "source_refs": ["https://www.postgresql.org/docs/18/sql-select.html"],
            "reference_answer": "Correct answer",
            "points": 1,
            "options": [
                {"text": "Correct answer", "correct": True},
                {"text": "Wrong answer A", "correct": False},
                {"text": "Wrong answer B", "correct": False},
                {"text": "Wrong answer C", "correct": False},
            ],
            "setup_sql": None,
            "edge_setup_sql": None,
            "rubrics": [],
        }
        return item


def _payload(concept, **updates):
    values = {
        "concept_ids": [concept.concept_id],
        "difficulties": ["HARD"],
        "source": "ai",
        "question_count": 3,
        "question_mix": {"mcq": 3},
        "assessment_style": "ADAPTIVE",
        "request_id": uuid4(),
    }
    values.update(updates)
    return practice.PracticeStart(**values)


def _correct_option(state, db):
    attempt = db.scalar(select(Attempt).where(Attempt.session_id == state.session_id))
    return next(option["option_id"] for option in attempt.question_snapshot["options"]
                if option["is_correct"])


def test_ai_adaptive_serves_validated_question_and_snapshot_source(
    db_session, sandbox_runner, monkeypatch
):
    from app.services import ai_adaptive
    monkeypatch.setattr(ai_adaptive, "_prefetch_after", lambda *args, **kwargs: None)
    _, learner, concepts = fixture(db_session)
    llm = FakeLLM(concepts[0].concept_id)
    state = practice.start(db_session, learner, _payload(concepts[0]), sandbox_runner, llm, locale="en")
    assert state.question_source == "ai"
    assert state.current_question.source == "ai_generated"
    snapshot = db_session.get(AssessmentSession, state.session_id).config_snapshot
    assert snapshot["source"] == "ai"
    attempt = db_session.scalar(select(Attempt).where(Attempt.session_id == state.session_id))
    assert attempt.question_snapshot["source"] == "ai_generated"


def test_ai_adaptive_difficulty_moves_up_after_a_correct_answer(
    db_session, sandbox_runner, monkeypatch
):
    from app.services import ai_adaptive
    monkeypatch.setattr(ai_adaptive, "_prefetch_after", lambda *args, **kwargs: None)
    _, learner, concepts = fixture(db_session)
    llm = FakeLLM(concepts[0].concept_id)
    state = practice.start(db_session, learner, _payload(concepts[0]), sandbox_runner, llm, locale="en")
    option_id = _correct_option(state, db_session)
    assessment_lifecycle.submit(
        db_session, state.session_id, learner,
        SubmitAnswerRequest(question_id=state.current_question.question_id,
                            selected_option_id=option_id),
        sandbox_runner,
    )
    served = adaptive_engine.serve_next(
        db_session, state.session_id, learner, runner=sandbox_runner, llm=llm
    )
    assert served.done is False
    assert served.question.difficulty_level == 5
    assert served.question.source == "ai_generated"


def test_ai_adaptive_falls_back_to_bank_without_exposing_the_error(
    db_session, sandbox_runner, monkeypatch
):
    from app.services import ai_adaptive
    monkeypatch.setattr(ai_adaptive, "_prefetch_after", lambda *args, **kwargs: None)
    _, learner, concepts = fixture(db_session)
    llm = FakeLLM(concepts[0].concept_id, fail=True)
    state = practice.start(db_session, learner, _payload(concepts[0]), sandbox_runner, llm, locale="en")
    assert state.question_source == "ai"
    assert state.current_question.source == "bank"
    attempt = db_session.scalar(select(Attempt).where(Attempt.session_id == state.session_id))
    assert attempt.grading_detail is None
    from app.models import SelectionLog
    log = db_session.scalar(select(SelectionLog).where(SelectionLog.session_id == state.session_id))
    assert log.is_fallback is True
    assert log.decision_detail["fallback_reason"] == "TimeoutError"
