"""AI #1 purity: the builder may format evidence, never grade or write feedback."""
import json
import re

import pytest

from app.services.prompt_builder import (
    MAX_PROMPT_BYTES,
    OUTPUT_FIELDS,
    build_prompt,
    template_prompt,
    validate_prompt,
)

DATA = {
    "version": "two-ai-v4",
    "mode": "attempt",
    "attempt_count": 1,
    "items": [
        {
            "attempt_id": 101,
            "question_id": 11,
            "type": "mcq",
            "prompt": "Which key uniquely identifies a row?",
            "answer": "candidate key",
            "points": "1",
            "score": "1",
            "reference_answer": "candidate key",
            "options": [],
            "concepts": ["Relational model"],
            "clo": ["CLO-1"],
            "topics": ["Database Design"],
            "difficulty": "Dễ",
            "rubric": [],
        },
        {
            "attempt_id": 102,
            "question_id": 12,
            "type": "essay",
            "prompt": "Explain lossless decomposition.",
            "answer": "ANSWER-SENTINEL-7f3c explains that joining the parts restores every original row.",
            "points": "2",
            "score": None,
            "reference_answer": "A lossless decomposition can be rejoined without spurious rows.",
            "options": [],
            "concepts": ["Normalization"],
            "clo": ["CLO-2"],
            "topics": ["Database Design"],
            "difficulty": "Vừa",
            "rubric": [{"level": "Complete", "min": "1.5", "max": "2", "criteria": "Explains join restoration"}],
        },
    ],
}


def sections(prompt):
    """Return only the three instruction sections; data/schema are evidence."""
    data = prompt.split("## DỮ LIỆU\n", 1)[1].split("## RUBRIC\n", 1)[0]
    schema = prompt.split("## SCHEMA JSON\n", 1)[1].split("## RÀNG BUỘC\n", 1)[0]
    return prompt.replace(data, "", 1).replace(schema, "", 1)


def test_template_prompt_is_one_prompt_with_no_grading_output():
    result = build_prompt(DATA)
    assert result.fallback_used and result.reason_code == "no_model"
    assert validate_prompt(result.prompt, DATA) == result.prompt
    assert result.prompt.count("## BỐI CẢNH\n") == 1
    assert result.prompt.count("## DỮ LIỆU\n") == 1
    assert result.prompt.count("## RUBRIC\n") == 1
    assert result.prompt.count("## SCHEMA JSON\n") == 1
    assert result.prompt.count("## RÀNG BUỘC\n") == 1
    # The learner answer is evidence exactly once; it is never rewritten into
    # a second feedback paragraph by the builder.
    assert result.prompt.count("ANSWER-SENTINEL-7f3c") == 1
    instructions = sections(result.prompt)
    for field in OUTPUT_FIELDS:
        assert not re.search(rf"(?<![\w]){field}\"?\s*:", instructions)
    assert '"question_comments"' not in instructions
    assert len(result.prompt.encode()) <= MAX_PROMPT_BYTES


def test_schema_section_is_instruction_only_and_matches_evaluation_model():
    prompt = template_prompt(DATA)
    schema = json.loads(prompt.split("## SCHEMA JSON\n", 1)[1].split("## RÀNG BUỘC\n", 1)[0])
    assert schema["title"] == "Evaluation"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(OUTPUT_FIELDS)


def test_practice_essay_cannot_reach_the_essay_only_grader(monkeypatch):
    """Practice essays belong to AI #2; the old grader must stay unreachable."""
    from types import SimpleNamespace
    from app.services import assessment_lifecycle, essay_grading
    from app.services.llm import LLMError

    called = []
    monkeypatch.setattr(essay_grading, "grade_essay", lambda *a, **k: called.append(1))
    monkeypatch.setattr(assessment_lifecycle, "question_view", lambda *_: SimpleNamespace(question_type="essay"))
    attempt = SimpleNamespace(question_snapshot={}, session=SimpleNamespace(config_snapshot={"learner_defined": True}))
    with pytest.raises(LLMError) as exc:
        assessment_lifecycle.grade_attempt(None, attempt, None, {"essay_answer": "answer"}, None, object())
    assert exc.value.code == LLMError.UNAVAILABLE
    assert not called
