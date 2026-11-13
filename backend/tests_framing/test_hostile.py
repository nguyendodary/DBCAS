"""Hostile-answer corpus and confinement tests."""
from __future__ import annotations

from dataclasses import replace
import json

from app.services.framing.hostile import corpus_stats, load_hostile_cases
from app.services.framing.util import canonical
from app.services.framing.validator import Framing, assemble_prompt, validate_prompt


def test_hostile_corpus_is_large_and_bilingual():
    cases = load_hostile_cases()
    stats = corpus_stats(cases)
    assert stats["count"] >= 50
    assert stats["languages"] == ["en", "vi"]
    assert len(stats["categories"]) >= 10
    assert len({case.id for case in cases}) == len(cases)


def test_every_hostile_answer_stays_inside_the_data_block(
    sample_data, sample_schema, sample_brief, sample_framing
):
    for case in load_hostile_cases():
        data = json.loads(json.dumps(sample_data, ensure_ascii=False))
        data["items"][1]["answer"] = case.answer
        prompt = assemble_prompt(data, sample_schema, sample_framing, brief=sample_brief)
        result = validate_prompt(prompt, data, sample_schema, sample_framing, brief=sample_brief)
        assert result.ok, (case.id, result.reason_code)
        context = prompt.split("## BỐI CẢNH\n", 1)[1].split("## DỮ LIỆU\n", 1)[0]
        assert canonical(case.answer) not in context
        assert prompt.count(canonical(case.answer)) == 1


def test_copying_a_hostile_answer_into_framing_is_rejected(
    sample_data, sample_schema, sample_brief, sample_framing
):
    for case in load_hostile_cases():
        data = json.loads(json.dumps(sample_data, ensure_ascii=False))
        data["items"][1]["answer"] = case.answer
        framing = replace(sample_framing, focus_text=case.answer)
        prompt = assemble_prompt(data, sample_schema, framing, brief=sample_brief)
        result = validate_prompt(prompt, data, sample_schema, framing, brief=sample_brief)
        assert not result.ok, case.id
        assert result.reason_code in {
            "focus_too_long", "focus_control", "focus_section", "focus_digit", "focus_grade",
            "focus_feedback", "focus_injection", "focus_pii", "focus_secret", "focus_url",
            "focus_answer_copy", "focus_concept_name", "focus_output_key", "prompt_sections",
        }, (case.id, result.reason_code)
