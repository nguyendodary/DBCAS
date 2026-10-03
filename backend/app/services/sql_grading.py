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
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import Account, Attempt, Question, SqlTestDataset
from ..repositories import AssessmentRepository
from ..schemas import AttemptResult, SubmitAnswerRequest
from . import sql_features, sql_result
from .sandbox_runner import SandboxError, SandboxRunner
from .session_guard import load_owned_active_session, load_served_attempt

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
        # Misconfigured fixture — cannot verify; count as failed and say so.
        entry["status"] = "error"
        entry["error_type"] = "invalid_expected_result"
        return entry

    try:
        schema = runner.provision_dataset(dataset.setup_sql)
    except SandboxError:
        raise
    try:
        result = runner.execute(sql_text, schema=schema)
    finally:
        runner.drop_dataset(schema)

    if not result.success:
        entry["status"] = "error"
        entry["error_type"] = result.error_type
        return entry

    outcome = sql_result.compare(result.columns, result.rows, expected)
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


def submit_sql_answer(
    db: Session,
    session_id: int,
    learner: Account,
    payload: SubmitAnswerRequest,
    runner: SandboxRunner,
) -> AttemptResult:
    """Grade a served SQL attempt; persists sql_answer, score, evidence."""
    repo = AssessmentRepository(db)
    load_owned_active_session(repo, session_id, learner)
    attempt = load_served_attempt(repo, session_id, payload.question_id)
    if attempt.submitted_at is not None:
        raise AppError(409, "already_submitted", "This question was already answered")

    question = attempt.question
    if question is None:
        raise AppError(404, "question_not_found", "Question not found")
    if question.question_type != "sql":
        raise AppError(
            422,
            "unsupported_question_type",
            "Only SQL answers are graded by this path",
        )
    if payload.sql_answer is None or not payload.sql_answer.strip():
        raise AppError(
            422, "empty_answer", "A SQL answer is required for this question"
        )

    datasets = repo.get_datasets_for_question(question.question_id)
    if not datasets:
        raise AppError(
            422,
            "dataset_not_configured",
            "This SQL question has no test dataset configured",
        )
    required = repo.get_required_concepts(question.question_id)

    try:
        result = grade_sql(
            question, datasets, required, payload.sql_answer, runner
        )
    except SandboxError as exc:
        raise AppError(503, exc.code, exc.message)

    _persist(attempt, payload.sql_answer, result)
    db.commit()
    db.refresh(attempt)

    return AttemptResult(
        attempt_id=attempt.attempt_id,
        session_id=attempt.session_id,
        question_id=attempt.question_id,
        score=attempt.score,
        points_possible=result["points_possible"],
        is_correct=result["is_correct"],
        submitted_at=attempt.submitted_at,
    )


def _persist(attempt: Attempt, sql_text: str, result: dict) -> None:
    attempt.sql_answer = sql_text
    attempt.score = result["score"]
    attempt.grading_detail = result["grading_detail"]
    attempt.submitted_at = datetime.now(timezone.utc)
