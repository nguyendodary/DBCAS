"""Load the read-only activated-content snapshot into a disposable test DB.

Test-only fixture: it never runs against the persistent development database.
Account, session, attempt, grading and audit rows are absent by construction.
"""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import text

from app.models import (
    Assessment,
    AssessmentConcept,
    CloConcept,
    Concept,
    ConceptDependency,
    CourseLearningOutcome,
    McqOption,
    Question,
    QuestionConcept,
    QuestionTranslation,
    Rubric,
    SqlTestDataset,
)

SNAPSHOT = Path(__file__).with_name("fixtures") / "release_content_snapshot.json"

# The activated benchmark assessment pre-dates the pack importer. The snapshot
# intentionally carries only the activated assessments 2/3/4/6, so this
# historical configuration is restored from the reviewed pack definition.
BENCHMARK = {
    "assessment_id": 1,
    "title": "Core PostgreSQL and Database Design Benchmark",
    "description": "Academic benchmark for SQL querying and relational design. "
                   "Adaptive 10 MCQ, 2 SQL and 1 essay in 60 minutes.",
    "max_questions": 13,
    "duration_min": 60,
    "target_mcq": 10,
    "target_sql": 2,
    "target_essay": 1,
    "status": "published",
    "family_id": None,
    "version_no": 1,
    "result_release_policy": "IMMEDIATE",
    "concept_codes": [
        "SQL-SELECT", "SQL-WHERE", "SQL-JOIN", "SQL-GROUP", "SQL-HAVING",
        "SQL-SUBQUERY", "DB-ER", "DB-NORM", "DB-FD", "DB-1NF", "DB-2NF", "DB-3NF",
    ],
}

SERIALS = [
    ("concept", "concept_id"),
    ("course_learning_outcome", "clo_id"),
    ("question", "question_id"),
    ("mcq_option", "option_id"),
    ("rubric", "rubric_id"),
    ("sql_test_dataset", "dataset_id"),
    ("assessment", "assessment_id"),
]


def _set_identity(db, generation):
    for table, column in SERIALS:
        db.execute(text(
            f"alter table {table} alter column {column} set generated {generation}"
        ))


def _reset_sequences(db):
    for table, column in SERIALS:
        db.execute(text(
            f"select setval(pg_get_serial_sequence('{table}', '{column}'), "
            f"(select coalesce(max({column}), 1) from {table}))"
        ))


def load(db, admin_id, path=SNAPSHOT):
    if not path.exists():
        raise FileNotFoundError(f"Release content snapshot is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))

    _set_identity(db, "by default")
    try:
        _insert_content(db, payload, admin_id)
        _reset_sequences(db)
    finally:
        _set_identity(db, "always")
    db.flush()
    return {
        "concept_ids": {
            row["concept_code"]: row["concept_id"] for row in payload["concepts"]
        },
        "question_ids": [row["question_id"] for row in payload["questions"]],
        "assessment_ids": [1, *[row["assessment_id"] for row in payload["assessments"]]],
        "localized_count": len(payload["question_translations"]),
        "missing_translation_keys": [],
    }


def _insert_content(db, payload, admin_id):
    db.execute(Concept.__table__.insert(), payload["concepts"])
    db.execute(CourseLearningOutcome.__table__.insert(), [
        {**row, "created_by": admin_id} for row in payload["course_learning_outcomes"]
    ])
    db.execute(CloConcept.__table__.insert(), payload["clo_concepts"])
    db.execute(ConceptDependency.__table__.insert(), payload["concept_dependencies"])

    benchmark = {key: value for key, value in BENCHMARK.items() if key != "concept_codes"}
    benchmark["created_by"] = admin_id
    assessments = [benchmark, *[
        {**row, "created_by": admin_id} for row in payload["assessments"]
    ]]
    db.execute(Assessment.__table__.insert(), assessments)

    concept_ids = {
        row["concept_code"]: row["concept_id"] for row in payload["concepts"]
    }
    missing = [code for code in BENCHMARK["concept_codes"] if code not in concept_ids]
    if missing:
        raise ValueError(f"Benchmark concept codes missing from snapshot: {missing}")
    db.execute(AssessmentConcept.__table__.insert(), [
        *payload["assessment_concepts"],
        *[
            {
                "assessment_id": 1,
                "concept_id": concept_ids[code],
                "min_difficulty": 1,
                "max_difficulty": 5,
                "target_pct": 60,
            }
            for code in BENCHMARK["concept_codes"]
        ],
    ])

    db.execute(Question.__table__.insert(), [
        {**row, "created_by": admin_id} for row in payload["questions"]
    ])
    db.execute(McqOption.__table__.insert(), payload["mcq_options"])
    db.execute(Rubric.__table__.insert(), payload["rubrics"])
    db.execute(SqlTestDataset.__table__.insert(), payload["sql_test_datasets"])
    db.execute(QuestionConcept.__table__.insert(), payload["question_concepts"])
    db.execute(QuestionTranslation.__table__.insert(), payload["question_translations"])
