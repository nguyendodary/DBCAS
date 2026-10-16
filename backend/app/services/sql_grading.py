"""UC15 — SQL answer verification and scoring (Task 3.3 / FR-09).

The learner statement is executed in the Docker sandbox against *every*
``sql_test_dataset`` configured for the question — regular and edge cases —
and the results are compared semantically against the stored
``expected_result`` (columns & rows). SQL source text is never compared; a
semantically equivalent formulation receives the same credit.

Scoring (deterministic):
* ``score = question.points * passed_datasets / total_datasets`` (2 dp).
* A required concept (``question_concept.is_required``) that is verifiable
  but absent zeroes the score — the mandated technique was not demonstrated.
* Execution errors fail the affected datasets.

Standardized evidence lands in ``attempt.grading_detail``; it deliberately
excludes ``expected_result`` contents and ``setup_sql`` so hidden answers and
setup data never reach the learner.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from ..errors import AppError
from ..models import Question, SqlTestDataset
from . import sql_features, sql_result
from .sandbox_runner import SandboxError, SandboxRunner

logger = logging.getLogger(__name__)

_CENT = Decimal("0.01")


def _evaluate_dataset(
    runner: SandboxRunner, dataset: SqlTestDataset, sql_text: str
) -> dict:
    """Provision the dataset, run learner SQL, compare, drop the schema."""
    expected = sql_result.parse_expected(dataset.expected_result)
    entry: dict = {
        "dataset": dataset.dataset_name,
        "is_edge_case": dataset.is_edge_case,
    }
    if expected is None:
        raise AppError(422, "invalid_expected_result", "This question has an invalid SQL fixture. Contact the administrator.")

    try:
        schema = runner.provision_dataset(dataset.setup_sql)
    except SandboxError:
        raise
    try:
        result = runner.execute(sql_text, schema=schema)
    finally:
        runner.drop_dataset(schema)

    if not result.success:
        if result.error_type == "sandbox_unavailable":
            raise SandboxError("sandbox_unavailable", "SQL grading is temporarily unavailable; the answer has not been scored")
        entry["status"] = "error"
        entry["error_type"] = result.error_type
        return entry

    outcome = sql_result.compare(result.columns, result.rows, expected, result.column_types)
    entry["status"] = outcome.status
    if outcome.matched:
        entry["matched_criteria"] = outcome.matched
    if outcome.failed:
        entry["failed_criteria"] = outcome.failed
    return entry


def grade_sql(
    question: Question,
    datasets: list[SqlTestDataset],
    required_concepts: list[str],
    sql_text: str,
    runner: SandboxRunner,
) -> dict:
    """Score a learner SQL statement. Pure wrt. persistence — returns the
    score plus the grading_detail evidence dict."""
    entries = [
        _evaluate_dataset(runner, ds, sql_text) for ds in datasets
    ]
    passed = sum(1 for e in entries if e["status"] == "passed")
    errored = next((e for e in entries if e["status"] == "error"), None)

    missing, unverified = sql_features.check_required(sql_text, required_concepts)

    if passed == len(datasets) and not missing:
        score = question.points
        status = "correct"
    elif passed > 0 and not missing:
        score = (
            question.points * Decimal(passed) / Decimal(len(datasets))
        ).quantize(_CENT, rounding=ROUND_HALF_UP)
        status = "partial"
    else:
        score = Decimal("0")
        status = "incorrect" if errored is None else "error"

    return {
        "score": score,
        "points_possible": question.points,
        "is_correct": status == "correct",
        "grading_detail": {
            "grader": "sql_semantic",
            "question_type": "sql",
            "status": status,
            "datasets_passed": passed,
            "datasets_total": len(datasets),
            "datasets": entries,
            "required_concepts": required_concepts,
            "missing_required_concepts": missing,
            "unverified_required_concepts": unverified,
            "points_possible": str(question.points),
            "points_earned": str(score),
        },
    }
