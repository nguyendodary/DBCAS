import copy
import logging
import pytest

from app.services.prompt_builder import build_prompt, template_prompt, validate_prompt
from app.services.evaluation_pipeline import evaluate, rule_evaluation, validate_evaluation


def test_large_attempt_keeps_feedback_for_every_question_and_hashes_full_answers(monkeypatch):
    from datetime import datetime, timezone
    from decimal import Decimal
    from types import SimpleNamespace
    from app.services import evaluation_service as service
    from app.services.prompt_builder import canonical
    session = SimpleNamespace(session_id=7, status="completed", release_status="published", started_at=datetime.now(timezone.utc))
    attempts = [SimpleNamespace(attempt_id=i, submitted_at=session.started_at, question_snapshot={},
        score=Decimal(1), essay_answer="Full learner answer " * 1000, sql_answer=None, review_revision=0) for i in range(1, 21)]
    question = SimpleNamespace(question_id=1, question_type="essay", points=Decimal(2), concept_tags=[],
        prompt="Long question " * 1000, reference_answer="Long reference " * 1000, options=[],
        difficulty_level=3, rubrics=[SimpleNamespace(level_name=level, min_score=0, max_score=2,
            criteria="Long rubric evidence " * 1000) for level in ("Irrelevant", "Relevant", "Partial", "Complete")])
    monkeypatch.setattr(service, "AssessmentRepository", lambda _: SimpleNamespace(
        sessions_for_learner=lambda _: [session], session_attempts=lambda _: attempts))
    monkeypatch.setattr(service, "question_view", lambda *_: question)
    data, _ = service.data_for(None, 1, 7)
    assert data["details_truncated"] and len(canonical(data).encode()) <= 165000
    assert [item["attempt_id"] for item in data["items"]] == list(range(1, 21))
    assert len(evaluate(data)["evaluation"]["question_comments"]) == 20
    assert validate_prompt(template_prompt(data), data)
    attempts[0].essay_answer += "Changed ending beyond the visible excerpt"
    changed, _ = service.data_for(None, 1, 7)
    assert changed["evidence_hash"] != data["evidence_hash"]


@pytest.fixture
def data():
    return {"mode": "attempt", "attempt_count": 1, "items": [
        {"attempt_id": 10, "question_id": 5, "type": "mcq", "points": "1", "score": "1", "answer": "A"},
        {"attempt_id": 11, "question_id": 6, "type": "essay", "points": "2", "score": None,
         "answer": "Khóa chính xác định duy nhất mỗi bản ghi", "reference_answer": "Khóa chính xác định duy nhất mỗi bản ghi"}]}


def test_template_sections_data_schema_and_no_grading(data):
    result = build_prompt(data)
    assert result.fallback_used
    assert validate_prompt(result.prompt, data) == result.prompt
    assert '"essay_score_proposal"' in result.prompt
    assert "## RUBRIC" in result.prompt


def test_local_model_valid_path_and_invalid_fallback(data):
    result = build_prompt(data, model_path="local", infer=lambda *_: template_prompt(data))
    assert not result.fallback_used
    for invalid in ["bad", template_prompt(data).replace('"answer":"A"', '"answer":"B"'), "x" * 200000]:
        result = build_prompt(data, model_path="local", infer=lambda *_: invalid)
        assert result.fallback_used
        assert result.prompt == template_prompt(data)


def test_inference_failure_falls_back_and_logs_metadata_only(data, caplog):
    def failure(*_):
        raise TimeoutError("secret-token")
    with caplog.at_level(logging.INFO, logger="dbcas.ai"):
        build_prompt(data, model_path="local", infer=failure)
        result = evaluate(data)
    assert result["evaluator_fallback"]
    assert "role=prompt_builder" in caplog.text and "role=evaluator" in caplog.text
    assert "duration_ms=" in caplog.text and "hash=" in caplog.text
    assert "secret-token" not in caplog.text and data["items"][1]["answer"] not in caplog.text


@pytest.mark.parametrize("mutation", [
    lambda x: x.update(extra="bad"),
    lambda x: x["question_comments"].pop(),
    lambda x: x["question_comments"].append(x["question_comments"][0]),
    lambda x: x["question_comments"][0].update(essay_score_proposal=1.0),
    lambda x: x["question_comments"][1].update(essay_score_proposal=3.0),
    lambda x: x["question_comments"][1].update(essay_score_proposal=float("nan")),
    lambda x: x.update(trend="invented"),
    lambda x: x.update(strengths=[""]),
])
def test_strict_evaluator_validation(data, mutation):
    value = copy.deepcopy(rule_evaluation(data))
    mutation(value)
    with pytest.raises(ValueError):
        validate_evaluation(value, data)


def test_external_path_and_invalid_response_fallback(data):
    class Provider:
        def is_configured(self): return True
        def generate_structured(self, task, messages, **kwargs):
            assert task == "attempt_evaluation"
            assert "## DỮ LIỆU" in messages[1].content
            return kwargs["validator"](rule_evaluation(data))
    assert not evaluate(data, Provider())["evaluator_fallback"]
    class Invalid(Provider):
        def generate_structured(self, *a, **kw): raise ValueError("invalid_json")
    assert evaluate(data, Invalid())["evaluator_fallback"]


def test_overall_has_trend_only_for_two_or_more(data):
    data.update(attempt_count=3, history=[{"percentage": "20"}, {"percentage": "60"}, {"percentage": "80"}])
    assert "+60.00" in rule_evaluation(data)["trend"]


def test_rule_feedback_uses_the_essay_proposal_instead_of_missing_score(data):
    essay = data["items"][1]
    essay.update(clo=["CLO-1"], topics=["Thiết kế"], difficulty="Dễ")
    data["dimensions"] = {"clo": [{"label": "CLO-1", "earned": "0", "possible": "2", "percentage": 0}]}
    original = copy.deepcopy(data)
    result = rule_evaluation(data)
    assert result["question_comments"][1]["essay_score_proposal"] == 2
    assert "điểm tối đa" in result["question_comments"][1]["comment"]
    assert not any("0.00%" in text for text in result["weaknesses"])
    assert data == original
