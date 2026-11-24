"""Mode 2 live generation against the real PostgreSQL test fixtures."""
import json
import re
from types import SimpleNamespace
from uuid import uuid4

import pytest

from sqlalchemy import select

from app.models import AssessmentSession, Attempt, QuestionCandidate
from app.schemas import CandidateApprovalRequest, SubmitAnswerRequest
from app.services import adaptive_engine, ai_admin_service, assessment_lifecycle, practice_service as practice
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
        kind = re.search(r"Create exactly one (mcq|sql|essay)", prompt).group(1)
        item = {
            "concept_ids": [self.concept_id],
            "difficulty_level": level,
            "question_type": kind,
            "prompt": f"AI generated {kind} {self.calls} for concept {self.concept_id} level {level}.",
            "explanation": "A deterministic generated explanation for this practice question.",
            "source_refs": ["https://www.postgresql.org/docs/18/sql-select.html"],
            "reference_answer": "Correct answer",
            "points": 1,
            "options": [],
            "setup_sql": None,
            "edge_setup_sql": None,
            "rubrics": [],
        }
        if kind == "mcq":
            item["options"] = [
                {"text": "Correct answer", "correct": True},
                {"text": "Wrong answer A", "correct": False},
                {"text": "Wrong answer B", "correct": False},
                {"text": "Wrong answer C", "correct": False},
            ]
        elif kind == "sql":
            item["reference_answer"] = "SELECT name FROM practice_rows ORDER BY id;"
            item["setup_sql"] = (
                "CREATE TABLE practice_rows(id int PRIMARY KEY, name text); "
                "INSERT INTO practice_rows VALUES (1,'alpha'),(2,'beta');"
            )
            item["edge_setup_sql"] = item["setup_sql"]
        else:
            item["reference_answer"] = "Normalization reduces duplicate data and update anomalies."
            item["rubrics"] = [
                {"level_name": "Incomplete", "min_score": 0, "max_score": 0.24,
                 "criteria": "No relevant explanation."},
                {"level_name": "Partial", "min_score": 0.25, "max_score": 0.49,
                 "criteria": "Some relevant explanation."},
                {"level_name": "Mostly Complete", "min_score": 0.50, "max_score": 0.74,
                 "criteria": "Mostly correct explanation."},
                {"level_name": "Complete", "min_score": 0.75, "max_score": 1,
                 "criteria": "Complete correct explanation."},
            ]
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


def test_ai_question_is_queued_and_approved_by_the_existing_admin_flow(
    db_session, sandbox_runner, monkeypatch
):
    from app.services import ai_adaptive
    monkeypatch.setattr(ai_adaptive, "_prefetch_after", lambda *args, **kwargs: None)
    admin, learner, concepts = fixture(db_session)
    concept = concepts[0]
    concept.description = "A detailed concept description used for deterministic generation."
    concept.keywords = ["select"]
    concept.learning_objectives = ["Write a correct SELECT statement"]
    db_session.commit()
    llm = FakeLLM(concept.concept_id)
    state = practice.start(db_session, learner, _payload(concept), sandbox_runner, llm, locale="en")
    candidate = db_session.scalar(select(QuestionCandidate).where(
        QuestionCandidate.payload["session_id"].astext == str(state.session_id)))
    assert candidate is not None
    assert candidate.payload["session_id"] == state.session_id
    detail = ai_admin_service.validate_candidate(db_session, candidate.candidate_id, sandbox_runner)
    assert detail.validation_status == "validated", detail.validation_detail
    approved = ai_admin_service.approve_candidate(
        db_session, candidate.candidate_id, admin,
        CandidateApprovalRequest(reviewed=True, content_hash=detail.validation_detail["content_hash"]),
        sandbox_runner,
    )
    assert approved.promoted_question_id is not None

    assessment_lifecycle.finalize(
        db_session, db_session.get(AssessmentSession, state.session_id), timed_out=True
    )
    db_session.commit()

    second = FakeLLM(concept.concept_id)
    state2 = practice.start(db_session, learner, _payload(concept, request_id=uuid4()),
                            sandbox_runner, second, locale="en")
    rejected_candidate = db_session.scalar(select(QuestionCandidate).where(
        QuestionCandidate.payload["session_id"].astext == str(state2.session_id)))
    assert rejected_candidate is not None
    rejected = ai_admin_service.reject_candidate(db_session, rejected_candidate.candidate_id, admin)
    assert rejected.validation_status == "rejected"


def test_ai_adaptive_supports_each_question_type(
    db_session, sandbox_runner, monkeypatch
):
    from app.services import ai_adaptive
    monkeypatch.setattr(ai_adaptive, "_prefetch_after", lambda *args, **kwargs: None)
    _, learner, concepts = fixture(db_session)
    for kind in ("mcq", "sql", "essay"):
        llm = FakeLLM(concepts[0].concept_id)
        state = practice.start(
            db_session, learner,
            _payload(concepts[0], question_count=3, question_mix={kind: 3}),
            sandbox_runner, llm, locale="en",
        )
        assert state.current_question.question_type == kind
        assert state.current_question.source == "ai_generated"
        assessment_lifecycle.finalize(
            db_session, db_session.get(AssessmentSession, state.session_id), timed_out=True
        )
        db_session.commit()
        db_session.expire_all()


def test_ai_adaptive_accepts_a_mixed_type_sequence(
    db_session, sandbox_runner, monkeypatch
):
    from app.services import ai_adaptive
    monkeypatch.setattr(ai_adaptive, "_prefetch_after", lambda *args, **kwargs: None)
    _, learner, concepts = fixture(db_session)
    state = practice.start(
        db_session, learner,
        _payload(concepts[0], question_count=3,
                 question_mix={"mcq": 1, "sql": 1, "essay": 1}),
        sandbox_runner, FakeLLM(concepts[0].concept_id), locale="en",
    )
    snapshot = db_session.get(AssessmentSession, state.session_id).config_snapshot
    assert snapshot["adaptive"]["type_sequence"] == ["mcq", "sql", "essay"]



def test_ability_moves_both_ways_and_grade_is_hidden_until_evidence(
    db_session, sandbox_runner, monkeypatch
):
    """is_correct is hidden by HUMAN_VERIFIED, not missing; ability does move."""
    from app.services import ai_adaptive
    monkeypatch.setattr(ai_adaptive, "_prefetch_after", lambda *args, **kwargs: None)
    _, learner, concepts = fixture(db_session)
    llm = FakeLLM(concepts[0].concept_id)
    payload = _payload(concepts[0], difficulties=["EASY"], question_count=3,
                       question_mix={"mcq": 3})
    state = practice.start(db_session, learner, payload, sandbox_runner, llm, locale="en")
    session_id = state.session_id

    def options_for(seq):
        attempt = db_session.scalar(
            select(Attempt).where(Attempt.session_id == session_id,
                                  Attempt.seq_no == seq)
        )
        return attempt.question_snapshot["options"]

    # Correct answer: score is persisted but hidden in the submit response.
    correct = next(o["option_id"] for o in options_for(1) if o["is_correct"])
    result = assessment_lifecycle.submit(
        db_session, session_id, learner,
        SubmitAnswerRequest(question_id=state.current_question.question_id,
                            selected_option_id=correct),
        sandbox_runner,
    )
    assert result.is_correct is None
    assert result.score is None
    served = adaptive_engine.serve_next(db_session, session_id, learner,
                                        runner=sandbox_runner, llm=llm)
    assert served.question.difficulty_level == 2  # EASY band 1..2: up

    wrong = next(o["option_id"] for o in options_for(2) if not o["is_correct"])
    assessment_lifecycle.submit(
        db_session, session_id, learner,
        SubmitAnswerRequest(question_id=served.question.question_id,
                            selected_option_id=wrong),
        sandbox_runner,
    )
    served = adaptive_engine.serve_next(db_session, session_id, learner,
                                        runner=sandbox_runner, llm=llm)
    assert served.question.difficulty_level == 1  # down

    correct = next(o["option_id"] for o in options_for(3) if o["is_correct"])
    assessment_lifecycle.submit(
        db_session, session_id, learner,
        SubmitAnswerRequest(question_id=served.question.question_id,
                            selected_option_id=correct),
        sandbox_runner,
    )
    adaptive_engine.finish_session(db_session, session_id, learner)
    progress = adaptive_engine.progress(
        db_session.get(AssessmentSession, session_id),
        db_session.scalars(select(Attempt).where(Attempt.session_id == session_id)).all(),
    )
    assert progress["ability"] == 2.0
    graded = db_session.scalars(
        select(Attempt).where(Attempt.session_id == session_id).order_by(Attempt.seq_no)
    ).all()
    assert [a.grading_detail["is_correct"] for a in graded] == [True, False, True]
    assert [str(a.score) for a in graded] == ["1.00", "0.00", "1.00"]
    assert db_session.get(AssessmentSession, session_id).release_status != "published"



class LegacyContractLLM(FakeLLM):
    """Provider that still uses the old `question` / string-options shape."""

    def generate_structured(self, *args, **kwargs):
        item = super().generate_structured(*args, **kwargs)
        item["question"] = item.pop("prompt")
        if item.get("options"):
            item["options"] = [option["text"] for option in item["options"]]
        return item


@pytest.mark.parametrize("kind", ["mcq", "sql", "essay"])
@pytest.mark.parametrize("locale", ["vi", "en"])
def test_prompt_names_the_schema_fields_and_carries_a_valid_example(kind, locale):
    from app.services import ai_adaptive
    from app.services.llm.provider import strict_wire_schema
    from app.services.llm.validation import validate_json_schema
    from app.services.practice_generation import GeneratedQuestion

    concept = SimpleNamespace(concept_id=16, concept_name="DML knowledge",
                              concept_code="SQL-DML-KNOW")
    text = ai_adaptive._prompt(concept, kind, 2, "EASY", locale)
    assert "Accept-Language" in text
    assert "Vietnamese" in text if locale == "vi" else "English" in text
    assert '"prompt"' in text and '"question":' not in text
    if kind == "mcq":
        assert '"text"' in text and '"correct"' in text
    if kind == "sql":
        assert '"setup_sql"' in text and '"edge_setup_sql"' in text and '"tables"' in text
    if kind == "essay":
        assert '"rubrics"' in text
    assert "additionalProperties" in text

    example_line = next(line for line in text.splitlines() if line.startswith("{"))
    example = json.loads(example_line)
    schema = GeneratedQuestion.model_json_schema()
    assert set(example) == set(schema["properties"])
    validate_json_schema(example, strict_wire_schema(schema))


def test_legacy_question_field_and_string_options_are_still_rejected(
    db_session, sandbox_runner, monkeypatch
):
    from app.services import ai_adaptive
    from app.models import SelectionLog
    monkeypatch.setattr(ai_adaptive, "_prefetch_after", lambda *args, **kwargs: None)
    _, learner, concepts = fixture(db_session)
    state = practice.start(db_session, learner, _payload(concepts[0]),
                           sandbox_runner, LegacyContractLLM(concepts[0].concept_id), locale="en")
    assert state.current_question.source == "bank"
    log = db_session.scalar(select(SelectionLog).where(SelectionLog.session_id == state.session_id))
    assert log.is_fallback is True
    assert log.decision_detail["fallback_reason"] == "generation_schema"



def test_dml_rotation_is_deterministic():
    from app.services.ai_adaptive import DML_KINDS, _target_dml_kind

    def served(verb):
        reference = {
            "INSERT": "INSERT INTO t VALUES (1);",
            "UPDATE": "UPDATE t SET id = 1 WHERE id = 1;",
            "DELETE": "DELETE FROM t WHERE id = 1;",
        }[verb]
        return SimpleNamespace(question_snapshot={"question_type": "sql", "reference_answer": reference})

    sequences = [[], ["INSERT"], ["INSERT", "UPDATE"],
                 ["INSERT", "UPDATE", "DELETE"], ["INSERT", "UPDATE", "DELETE", "INSERT"]]
    assert [_target_dml_kind([served(v) for v in seq]) for seq in sequences] == [
        "INSERT", "UPDATE", "DELETE", "INSERT", "UPDATE"]
    assert DML_KINDS == ("INSERT", "UPDATE", "DELETE")


@pytest.mark.parametrize("target", ["INSERT", "UPDATE", "DELETE"])
def test_prompt_carries_dml_target_and_matching_example(target):
    from app.services import ai_adaptive
    concept = SimpleNamespace(concept_id=16, concept_name="DML knowledge",
                              concept_code="SQL-DML-KNOW")
    text = ai_adaptive._prompt(concept, "sql", 2, "MEDIUM", "en", target)
    assert "if it is DML it MUST" in text and target in text
    if target in ("UPDATE", "DELETE"):
        assert "never RETURNING" in text
    example = json.loads(next(line for line in text.splitlines() if line.startswith("{")))
    assert ai_adaptive._dml_statement_kind(example["reference_answer"]) == target


class FixedLLM:
    """Provider returning one exact generated object."""

    def __init__(self, item):
        self.item = item

    def is_configured(self):
        return True

    def with_budget(self, **_kwargs):
        return self

    def generate_structured(self, *_args, **_kwargs):
        return self.item


def test_wrong_dml_kind_is_rejected_and_falls_back_to_bank(
    db_session, sandbox_runner, monkeypatch, caplog
):
    from app.services import ai_adaptive
    monkeypatch.setattr(ai_adaptive, "_prefetch_after", lambda *args, **kwargs: None)
    monkeypatch.setattr(ai_adaptive, "_target_dml_kind", lambda _attempts: "UPDATE")
    _, learner, concepts = fixture(db_session)
    from app.config import get_settings
    from app.services.sandbox_runner import SandboxRunner
    writable = SandboxRunner(get_settings().model_copy(update={"sandbox_writable": True}))
    example = json.loads(ai_adaptive._example_question(concepts[0], "sql", 4, "en", "INSERT"))
    state = practice.start(db_session, learner, _payload(concepts[0], question_count=3,
                                                          question_mix={"sql": 3}),
                           writable, FixedLLM(example), locale="en")
    assert state.current_question.source == "bank"
    from app.models import SelectionLog
    log = db_session.scalar(select(SelectionLog).where(SelectionLog.session_id == state.session_id))
    assert log.is_fallback is True
    assert log.decision_detail["fallback_reason"] == "ValueError"
    assert "dml_kind_mismatch" in caplog.text
