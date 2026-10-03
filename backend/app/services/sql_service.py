"""UC13 — run learner SQL in the embedded editor.

Provisions the question's primary (non-edge) test dataset in the sandbox,
executes the learner statement there via the Sandbox Runner, and returns the
sanitized structured result. Nothing is submitted or scored here — grading is
the submit-answer flow.
"""

from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import Account
from ..repositories import AssessmentRepository
from ..schemas import RunSqlRequest, SqlRunResult
from .sandbox_runner import SandboxError, SandboxRunner
from .session_guard import load_owned_active_session, load_served_attempt


def run_learner_sql(
    db: Session,
    session_id: int,
    learner: Account,
    payload: RunSqlRequest,
    runner: SandboxRunner,
) -> SqlRunResult:
    repo = AssessmentRepository(db)
    load_owned_active_session(repo, session_id, learner)
    attempt = load_served_attempt(repo, session_id, payload.question_id)
    question = attempt.question
    if question.question_type != "sql":
        raise AppError(
            422,
            "unsupported_question_type",
            "Only SQL questions can be executed by this endpoint",
        )

    datasets = repo.get_datasets_for_question(question.question_id)
    primary = next((d for d in datasets if not d.is_edge_case), None)
    if primary is None:
        raise AppError(
            422,
            "dataset_not_configured",
            "This SQL question has no test dataset configured",
        )

    try:
        schema = runner.provision_dataset(primary.setup_sql)
    except SandboxError as exc:
        raise AppError(503, exc.code, exc.message)
    try:
        result = runner.execute(payload.sql, schema=schema)
    finally:
        runner.drop_dataset(schema)

    return SqlRunResult(
        success=result.success,
        columns=result.columns,
        rows=result.rows,
        row_count=result.row_count,
        execution_time_ms=result.execution_time_ms,
        error_type=result.error_type,
        error_message=result.error_message,
    )
