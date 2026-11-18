"""PR 3A migration 026 schema and concurrency regressions.

These use the same disposable PostgreSQL that conftest.py provisions. The
standalone runner scripts/verify_pr3a_schema.py can execute the same checks
without pytest when Docker is unavailable.
"""
import os
import sys
import uuid
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

SCHEMA_SQL = ROOT / "db" / "schema.sql"
MIGRATION_026 = ROOT / "db" / "migrations" / "026_pr3a_database_foundation.sql"
BEGIN_MARKER = (
    "-- PR 3A MIGRATION 026 BEGIN "
    "(mirrored from db/migrations/026_pr3a_database_foundation.sql)"
)
END_MARKER = (
    "-- PR 3A MIGRATION 026 END "
    "(mirrored from db/migrations/026_pr3a_database_foundation.sql)"
)
PR3A_TABLES = {
    "question_rubric_profile", "question_rubric_criterion", "attempt_rubric_criterion",
    "session_result_version", "session_result_version_score",
    "session_result_criterion_score", "session_result_publication",
    "session_result_analysis", "ai_stage_run", "ai_stage_validation",
    "ai_stage_attempt", "ai_prompt_record", "ai_prompt_content",
    "retention_purge_audit", "prompt_access_audit",
}

# The four catalog sets that must agree between schema.sql and the migration.
TABLES_SQL = """select c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where n.nspname=current_schema() and c.relkind='r' and c.relpersistence='p'
 order by c.relname collate "C" """
COLUMNS_SQL = """select table_name, column_name, data_type, udt_name, is_nullable,
 column_default, is_identity, character_maximum_length, numeric_precision, numeric_scale
 from information_schema.columns
 where table_schema=current_schema() and table_name<>'schema_migration'
 order by table_name, column_name"""
CONSTRAINTS_SQL = """select c.relname, con.conname, con.contype, pg_get_constraintdef(con.oid)
 from pg_constraint con join pg_class c on c.oid=con.conrelid
 join pg_namespace n on n.oid=c.relnamespace
 where n.nspname=current_schema() and c.relname<>'schema_migration'
 order by c.relname, con.conname collate "C" """
INDEXES_SQL = """select tablename, indexname,
 regexp_replace(indexdef, current_schema(), 'SCHEMA', 'g')
 from pg_indexes
 where schemaname=current_schema() and tablename<>'schema_migration'
 order by tablename collate "C", indexname collate "C" """


def _dsn():
    value = os.environ.get("DATABASE_URL") or os.environ.get("PR3A_TEST_DSN")
    assert value, "DATABASE_URL is required"
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def _catalog_shape(conn):
    """Return the table, column, constraint and index sets of the current schema."""
    return {
        "tables": tuple(r[0] for r in conn.execute(TABLES_SQL).fetchall()),
        "columns": tuple(tuple(r) for r in conn.execute(COLUMNS_SQL).fetchall()),
        "constraints": tuple(tuple(r) for r in conn.execute(CONSTRAINTS_SQL).fetchall()),
        "indexes": tuple(tuple(r) for r in conn.execute(INDEXES_SQL).fetchall()),
    }


def _load_shape(conn, namespace, sql):
    conn.execute(f'DROP SCHEMA IF EXISTS "{namespace}" CASCADE')
    conn.execute(f'CREATE SCHEMA "{namespace}"')
    conn.execute(f'SET search_path TO "{namespace}"')
    try:
        conn.execute(sql, prepare=False)
        return _catalog_shape(conn)
    finally:
        conn.execute("SET search_path TO public")
        conn.execute(f'DROP SCHEMA IF EXISTS "{namespace}" CASCADE')


def test_026_schema_sql_matches_migration_chain_catalog():
    """db/schema.sql carries the 026 DDL: loading it alone must match the chain.

    One isolated schema loads db/schema.sql as-is (what introspection sees);
    a second loads the same file with the mirrored 026 block removed and then
    applies the real migration. Their table/column/constraint/index sets must
    be byte-for-byte identical, and re-applying the migration must be a no-op.
    """
    schema_sql = SCHEMA_SQL.read_text(encoding="utf-8")
    assert BEGIN_MARKER in schema_sql and END_MARKER in schema_sql
    before, rest = schema_sql.split(BEGIN_MARKER, 1)
    _, after = rest.split(END_MARKER, 1)
    without_026 = before + after
    migration_sql = MIGRATION_026.read_text(encoding="utf-8")

    token = uuid.uuid4().hex[:10]
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        embedded = _load_shape(conn, f"pr3a_embedded_{token}", schema_sql)
        chain = _load_shape(conn, f"pr3a_chain_{token}", without_026 + "\n" + migration_sql)
        reapply = _load_shape(conn, f"pr3a_reapply_{token}", schema_sql + "\n" + migration_sql)

    assert PR3A_TABLES <= set(embedded["tables"])
    assert PR3A_TABLES <= set(chain["tables"])
    for kind in ("tables", "columns", "constraints", "indexes"):
        assert embedded[kind] == chain[kind], f"schema.sql vs migration chain differ in {kind}"
        assert embedded[kind] == reapply[kind], f"migration 026 re-application drifted {kind}"


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
