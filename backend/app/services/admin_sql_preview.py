"""Preview unsaved answers using the existing isolated, read-only SQL runner."""
from dataclasses import asdict

from ..errors import AppError
from ..schemas import AdminSqlPreviewRequest, SqlRunResult
from .sandbox_runner import SandboxError, SandboxRunner
from .sql_validator import validate_learner_sql


def preview_sql(payload: AdminSqlPreviewRequest, runner: SandboxRunner) -> SqlRunResult:
    issue = validate_learner_sql(payload.sql)
    if issue:
        return SqlRunResult(success=False, error_type=issue[0], error_message=issue[1])
    try:
        schema = runner.provision_dataset(payload.setup_sql)
        try:
            result = runner.execute(payload.sql, schema=schema)
        finally:
            runner.drop_dataset(schema)
    except SandboxError as exc:
        raise AppError(503 if exc.code == "sandbox_unavailable" else 422, exc.code, exc.message) from None
    return SqlRunResult(**asdict(result))
