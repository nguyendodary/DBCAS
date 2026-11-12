"""Standalone framing tests: no database, Docker, provider or live model."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.framing.util import canonical  # noqa: E402
from app.services.framing.validator import (  # noqa: E402
    DEFAULT_SECTIONS, Framing, assemble_prompt,
)


@pytest.fixture()
def sample_data():
    return {
        "version": "two-ai-v4",
        "mode": "attempt",
        "attempt_count": 1,
        "score": {"earned": "3.00", "possible": "5.00", "percentage": 60.0},
        "history": [{"session_id": 7, "ordinal": 1, "date": "2026-11-10T00:00:00+00:00",
                     "earned": "3.00", "possible": "5.00", "percentage": 60.0}],
        "dimensions": {
            "clo": [{"label": "CLO-1", "earned": "1.00", "possible": "2.00", "percentage": 50.0}],
            "topic": [{"label": "Thiết kế CSDL", "earned": "1.00", "possible": "2.00", "percentage": 50.0}],
            "difficulty": [{"label": "Vừa", "earned": "2.00", "possible": "3.00", "percentage": 66.67}],
        },
        "items": [
            {"attempt_id": 10, "question_id": 5, "type": "mcq", "points": "1", "score": "1", "answer": "A"},
            {"attempt_id": 11, "question_id": 6, "type": "essay", "points": "2", "score": None,
             "answer": "Khóa chính xác định duy nhất mỗi bản ghi và khóa ngoại bảo toàn tham chiếu.",
             "reference_answer": "Khóa chính định danh duy nhất; khóa ngoại bảo toàn tham chiếu."},
        ],
        "recurring_weaknesses": [{"concept": "Chuẩn hóa", "attempts": 2}],
        "evidence_hash": "0" * 64,
        "history_hash": "1" * 64,
        "details_truncated": False,
    }


@pytest.fixture()
def sample_schema():
    return {
        "title": "Evaluation",
        "type": "object",
        "additionalProperties": False,
        "required": ["summary", "question_comments"],
        "properties": {"summary": {"type": "string"}, "question_comments": {"type": "array"}},
    }


@pytest.fixture()
def sample_brief():
    return {
        "mode": "attempt",
        "attempt_count": 1,
        "score_percentage": 60.0,
        "weak_concepts": [
            {"name": "Chuẩn hóa", "percentage": 37.5},
            {"name": "Khóa ngoại", "percentage": 50.0},
        ],
        "strong_concepts": [{"name": "Khóa chính", "percentage": 90.0}],
        "essay_count": 1,
        "mcq_count": 1,
        "sql_count": 0,
        "trend": "up",
        "details_truncated": False,
    }


@pytest.fixture()
def sample_framing():
    return Framing(
        task_text="Hãy tạo phần mô tả nhiệm vụ đánh giá dựa trên bằng chứng và rubric, bằng tiếng Việt.",
        focus_text="Tập trung vào các chủ đề được hệ thống nêu và chỉ rõ giới hạn khi dữ liệu chưa đầy đủ.",
        focus_concepts=("Chuẩn hóa",),
        format_text=None,
    )


@pytest.fixture()
def sample_prompt(sample_data, sample_schema, sample_brief, sample_framing):
    return assemble_prompt(sample_data, sample_schema, sample_framing, brief=sample_brief)


def section_bodies(prompt: str, sections=DEFAULT_SECTIONS):
    rest = prompt
    bodies = {}
    for index, name in enumerate(sections):
        body, separator, rest = rest.partition(f"## {name}\n")
        assert separator, f"missing section {name}"
        if index:
            bodies[sections[index - 1]] = body.strip()
    bodies[sections[-1]] = rest.strip()
    return bodies


__all__ = ["canonical", "section_bodies"]
