"""Dependency readiness, distinct from the process liveness endpoint."""
import logging
from sqlalchemy.exc import SQLAlchemyError
from ..repositories import ReadinessRepository

def dependency_status(db, sandbox):
    try:
        database_ready = ReadinessRepository(db).check_schema()
    except SQLAlchemyError as exc:
        logging.getLogger(__name__).warning("Database readiness failed: %s", type(exc).__name__)
        db.rollback()
        database_ready = False
    sandbox_ready = sandbox.is_ready()
    return {"database": database_ready, "sandbox": sandbox_ready}
