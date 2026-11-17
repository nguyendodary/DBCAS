"""PR 3A migration 026 schema and concurrency regressions.

These use the same disposable PostgreSQL that conftest.py provisions. The
standalone runner scripts/verify_pr3a_schema.py can execute the same checks
without pytest when Docker is unavailable.
"""
import os
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_pr3a_schema import (  # noqa: E402
    check_ai_uniqueness_and_ordering,
    check_completeness_failures,
    check_legacy_workflow,
    check_migration_text,
    check_result_completeness,
    check_schema_shape,
)


def _dsn():
    value = os.environ.get("DATABASE_URL") or os.environ.get("PR3A_TEST_DSN")
    assert value, "DATABASE_URL is required"
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def test_026_migration_text_is_consistent():
    check_migration_text()


def test_026_schema_shape_and_session_scoped_index():
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        check_schema_shape(conn)


def test_026_ai_uniqueness_regex_and_stage_ordering():
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        check_ai_uniqueness_and_ordering(conn)


def test_026_result_completeness_publication_and_freeze():
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        check_result_completeness(conn)


def test_026_deferred_completeness_failures():
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        check_completeness_failures(conn)


def test_026_legacy_attempt_workflow_is_unaffected():
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        check_legacy_workflow(conn)
