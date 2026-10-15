"""Explicit, narrowly guarded repair; historical evidence is never rewritten."""
from sqlalchemy import select

from ..errors import AppError
from ..models import Attempt
from ..schemas import RubricInput
from .rubric_validation import rubric_problems


HISTORICAL_INDEX_RUBRIC = [
    {"level_name": "Missing", "min_score": 0, "max_score": 0, "criteria": "No relevant content"},
    {"level_name": "Partial", "min_score": 1, "max_score": 3, "criteria": "Mentions lookup benefit OR write cost"},
    {"level_name": "Complete", "min_score": 4, "max_score": 5, "criteria": "Covers B-tree lookup cost and write amplification"},
]


def repair_index_rubric(db, repo, question, source, actual, proposed):
    if (source.get("key") != "legacy-essay-index-read-write"
            or source.get("concept_codes") != ["IDX"]
            or question.prompt != "Explain why indexes speed up reads but slow down writes."
            or question.question_type != "essay" or question.points != 5
            or question.difficulty_level != 3):
        return False
    before, after = actual.model_dump(), proposed.model_dump()
    for value in (before, after):
        value.pop("translations", None)
        value.pop("rubrics", None)
        for key in ("concept_ids", "required_concept_ids"):
            value[key].sort()
    historical = [RubricInput(**row).model_dump() for row in HISTORICAL_INDEX_RUBRIC]
    if before != after or sorted(actual.model_dump()["rubrics"], key=lambda row: row["min_score"]) != historical:
        return False
    problems = rubric_problems(proposed.rubrics, proposed.points)
    if problems:
        raise AppError(422, "invalid_rubric", "The proposed repair must satisfy the canonical rubric contract")
    attempts = db.scalars(select(Attempt).where(Attempt.question_id == question.question_id)).all()
    if any(not attempt.question_snapshot or not attempt.question_snapshot.get("rubrics") for attempt in attempts):
        raise AppError(409, "legacy_evidence_requires_snapshot",
                       "The rubric repair requires preserved rubric snapshots for every historical attempt")
    repo.replace_rubrics(question, proposed.rubrics)
    question.version_no += 1
    db.flush()
    db.expire(question, ["rubrics"])
    return True
