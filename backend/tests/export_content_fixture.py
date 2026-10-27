"""Read-only export of activated academic content for disposable browser tests.

Only curriculum, question-bank, translation and assessment rows are copied.
Accounts, sessions, attempts, reviews, caches and audit rows are deliberately
excluded so mutating E2E never touches personal or historical data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import psycopg

TABLES = {
    "concepts": (
        "select concept_id, concept_code, concept_name, subject_area, description, "
        "difficulty_level, sql_feature, keywords, learning_objectives from concept "
        "order by concept_id",
    ),
    "course_learning_outcomes": (
        "select clo_id, clo_code, title, description, status "
        "from course_learning_outcome order by clo_id",
    ),
    "clo_concepts": (
        "select clo_id, concept_id, mapping_source, status "
        "from clo_concept order by clo_id, concept_id",
    ),
    "concept_dependencies": (
        "select concept_id, prerequisite_concept_id from concept_dependency "
        "order by concept_id, prerequisite_concept_id",
    ),
    "assessments": (
        "select assessment_id, title, description, max_questions, duration_min, "
        "target_mcq, target_sql, target_essay, status, family_id, version_no, "
        "result_release_policy from assessment where assessment_id in (2,3,4,6) "
        "order by assessment_id",
    ),
    "assessment_concepts": (
        "select assessment_id, concept_id, min_difficulty, max_difficulty, target_pct "
        "from assessment_concept where assessment_id in (2,3,4,6) "
        "order by assessment_id, concept_id",
    ),
    "questions": (
        "select question_id, question_type, prompt, reference_answer, difficulty_level, "
        "points, source, status, family_id, version_no, explanation, tags, source_refs, "
        "original_locale, ai_review from question order by question_id",
    ),
    "mcq_options": (
        "select option_id, question_id, option_label, option_text, is_correct "
        "from mcq_option order by option_id",
    ),
    "rubrics": (
        "select rubric_id, question_id, level_name, min_score, max_score, criteria "
        "from rubric order by rubric_id",
    ),
    "sql_test_datasets": (
        "select dataset_id, question_id, dataset_name, setup_sql, expected_result, "
        "is_edge_case from sql_test_dataset order by dataset_id",
    ),
    "question_concepts": (
        "select question_id, concept_id, tag_source, is_required, confirmed, review_status "
        "from question_concept order by question_id, concept_id",
    ),
    "question_translations": (
        "select question_id, locale, source_hash, prompt, explanation, option_texts, rubrics "
        "from question_translation order by question_id, locale",
    ),
}


def rows(conn, sql):
    with conn.cursor() as cursor:
        cursor.execute(sql)
        columns = [column.name for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime,)):
        return value.isoformat()
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--confirm-database", required=True,
        help="Refuse unless the server reports this exact database name",
    )
    args = parser.parse_args()
    with psycopg.connect(
        args.dsn, options="-c default_transaction_read_only=on"
    ) as conn:
        database = conn.execute("select current_database()").fetchone()[0]
        if database != args.confirm_database:
            raise SystemExit(f"Connected to {database!r}, expected {args.confirm_database!r}")
        payload = {
            "meta": {
                "provenance": (
                    "Read-only export of the activated academic content. "
                    "No accounts, sessions, attempts or review records are included."
                ),
                "source_database": database,
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }
        }
        for key, (sql,) in TABLES.items():
            payload[key] = rows(conn, sql)
        payload["meta"]["counts"] = {key: len(payload[key]) for key in TABLES}

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), default=json_default
    )
    output.write_text(serialized + "\n", encoding="utf-8")
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    print(json.dumps({
        "output": str(output),
        "bytes": len(serialized),
        "sha256": digest,
        "counts": payload["meta"]["counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
