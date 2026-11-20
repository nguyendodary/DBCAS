"""Step 2 — exhaustive AST classification / read-only script policy tests.

Every case here is synthetic. The matrix covers statement kinds, multi-statement
parsing, and the parser-bypass classes enumerated in docs/sql-sandbox/04 §4.2.
"""

import pytest

from app.services.sql_classifier import (
    DDL, FORBIDDEN, READ_ONLY, WRITE_DML, classify_script,
    validate_read_only_script,
)
from app.services.sql_validator import validate_learner_sql

ALLOWED = frozenset({"ds_abc123def456"})


# --------------------------------------------------------------------------
# Typed classification
# --------------------------------------------------------------------------

@pytest.mark.parametrize("sql,expected", [
    ("SELECT 1", READ_ONLY),
    ("VALUES (1)", READ_ONLY),
    ("SELECT 1 UNION SELECT 2", READ_ONLY),
    ("WITH x AS (SELECT 1) SELECT * FROM x", READ_ONLY),
    ("INSERT INTO t VALUES (1)", WRITE_DML),
    ("UPDATE t SET a = 1", WRITE_DML),
    ("DELETE FROM t", WRITE_DML),
    ("MERGE INTO t USING s ON true WHEN MATCHED THEN DELETE", WRITE_DML),
    ("CREATE TABLE t (a int)", DDL),
    ("ALTER TABLE t ADD COLUMN b int", DDL),
    ("DROP TABLE t", DDL),
    ("TRUNCATE t", DDL),
    ("SET search_path = public", FORBIDDEN),
    ("COPY t FROM STDIN", FORBIDDEN),
    ("DO $$ BEGIN NULL; END $$", FORBIDDEN),
    ("BEGIN", FORBIDDEN),
    ("COMMIT", FORBIDDEN),
    ("GRANT SELECT ON t TO x", FORBIDDEN),
    ("EXPLAIN SELECT 1", FORBIDDEN),
])
def test_root_classification(sql, expected):
    result = classify_script(sql)
    assert result.ok, result
    assert result.statements[0].kind == expected


def test_multi_statement_offsets_with_dollar_quote_and_comments():
    sql = "-- lead\nSELECT 1; /* c */ SELECT $$a;b$$ AS x;\nSELECT 3"
    result = classify_script(sql)
    assert result.ok
    assert len(result.statements) == 3
    assert [s.index for s in result.statements] == [1, 2, 3]
    assert all(s.kind == READ_ONLY for s in result.statements)
    assert result.statements[0].sql == "SELECT 1"
    assert "$$a;b$$" in result.statements[1].sql
    assert result.statements[2].sql == "SELECT 3"


def test_too_many_statements_fails_closed():
    result = classify_script(";".join(["SELECT 1"] * 33), max_statements=32)
    assert not result.ok
    assert result.error_type == "too_many_statements"


@pytest.mark.parametrize("sql,error_type", [
    ("", "empty_query"),
    ("   \n\t ", "empty_query"),
    ("SELECT 'unterminated", "syntax_error"),
    ("SELECT 1\x00", "invalid_input"),
])
def test_classify_fail_closed(sql, error_type):
    result = classify_script(sql)
    assert not result.ok
    assert result.error_type == error_type


# --------------------------------------------------------------------------
# Read-only script policy — accepted
# --------------------------------------------------------------------------

@pytest.mark.parametrize("sql", [
    "SELECT 1",
    "SELECT 1; SELECT 2; SELECT 3",
    "-- comment only\nSELECT 1 /* inline */; SELECT 2",
    "SELECT $$semi;colon$$ AS s",
    "WITH x AS (SELECT 1 AS n) SELECT n FROM x",
    "SELECT 1 UNION ALL SELECT 2",
    "VALUES (1), (2)",
    "SELECT a FROM sales GROUP BY a ORDER BY a LIMIT 5",
    "SELECT \"MixedCase\" FROM \"MyTable\"",
])
def test_read_only_accepted(sql):
    assert validate_read_only_script(sql, allowed_schemas=ALLOWED) is None


# --------------------------------------------------------------------------
# Read-only script policy — rejected (bypass matrix)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("sql,error_type", [
    # write DML (top level and via data-modifying CTE)
    ("INSERT INTO t VALUES (1)", "prohibited_statement"),
    ("UPDATE t SET a = 1", "prohibited_statement"),
    ("DELETE FROM t", "prohibited_statement"),
    ("MERGE INTO t USING s ON true WHEN MATCHED THEN DELETE", "prohibited_statement"),
    ("WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x", "prohibited_statement"),
    ("WITH x AS (INSERT INTO t VALUES (1) RETURNING *) SELECT * FROM x", "prohibited_statement"),
    ("WITH x AS (UPDATE t SET a = 1 RETURNING *) SELECT * FROM x", "prohibited_statement"),
    # SELECT INTO / locking reads
    ("SELECT 1 INTO newt", "prohibited_statement"),
    ("SELECT * FROM t FOR UPDATE", "prohibited_statement"),
    ("SELECT * FROM t FOR SHARE", "prohibited_statement"),
    # DDL
    ("CREATE TABLE t (a int)", "prohibited_statement"),
    ("ALTER TABLE t ADD COLUMN b int", "prohibited_statement"),
    ("DROP TABLE t", "prohibited_statement"),
    ("TRUNCATE t", "prohibited_statement"),
    ("CREATE TEMP TABLE t (a int)", "prohibited_statement"),
    ("CREATE INDEX i ON t (a)", "prohibited_statement"),
    ("CREATE VIEW v AS SELECT 1", "prohibited_statement"),
    # transaction-control escape attempts
    ("BEGIN; SELECT 1; COMMIT", "prohibited_statement"),
    ("SELECT 1; ROLLBACK", "prohibited_statement"),
    ("SAVEPOINT s", "prohibited_statement"),
    ("RELEASE s", "prohibited_statement"),
    ("PREPARE TRANSACTION 'x'", "prohibited_statement"),
    # session / privilege commands
    ("SET search_path = public", "prohibited_statement"),
    ("RESET ALL", "prohibited_statement"),
    ("SET ROLE postgres", "prohibited_statement"),
    ("SET SESSION AUTHORIZATION postgres", "prohibited_statement"),
    ("GRANT SELECT ON t TO x", "prohibited_statement"),
    ("REVOKE SELECT ON t FROM x", "prohibited_statement"),
    ("ALTER SYSTEM SET work_mem = '1MB'", "prohibited_statement"),
    ("ALTER ROLE x CREATEDB", "prohibited_statement"),
    ("CREATE ROLE x", "prohibited_statement"),
    ("CREATE EXTENSION dblink", "prohibited_statement"),
    ("CREATE FUNCTION f() RETURNS int AS $$ SELECT 1 $$ LANGUAGE sql", "prohibited_statement"),
    ("COPY t FROM STDIN", "prohibited_statement"),
    ("DO $$ BEGIN NULL; END $$", "prohibited_statement"),
    ("CALL p()", "prohibited_statement"),
    ("EXPLAIN SELECT 1", "prohibited_statement"),
    ("LOCK TABLE t", "prohibited_statement"),
    ("VACUUM", "prohibited_statement"),
    ("LISTEN chan", "prohibited_statement"),
    ("DISCARD ALL", "prohibited_statement"),
    # unsafe functions
    ("SELECT pg_sleep(10)", "unsafe_function"),
    ("SELECT dblink('x')", "unsafe_function"),
    ("SELECT lo_import('/etc/passwd')", "unsafe_function"),
    ("SELECT pg_read_file('x')", "unsafe_function"),
    ("SELECT nextval('s')", "unsafe_function"),
    ("SELECT set_config('x','y',false)", "unsafe_function"),
    ("SELECT pg_catalog.pg_sleep(1)", "unsafe_function"),
    # catalog / cross-schema access
    ("SELECT * FROM pg_catalog.pg_class", "forbidden_schema"),
    ("SELECT * FROM information_schema.tables", "forbidden_schema"),
    ("SELECT * FROM ds_other12345.t", "forbidden_schema"),
    ("SELECT * FROM public.t", None),  # public stays allowed in read-only
    ("SELECT * FROM otherdb.public.t", "forbidden_schema"),
    ("SELECT * FROM pg_temp.t", "forbidden_schema"),
    # parse / input failures
    ("SELECT 'unterminated", "syntax_error"),
    ("SELECT 1\x00", "invalid_input"),
])
def test_read_only_rejected(sql, error_type):
    issue = validate_read_only_script(sql, allowed_schemas=ALLOWED)
    if error_type is None:
        assert issue is None
    else:
        assert issue is not None
        assert issue[0] == error_type, (sql, issue)


def test_rejection_reports_statement_index():
    issue = validate_read_only_script(
        "SELECT 1; SELECT 2; INSERT INTO t VALUES (1)", allowed_schemas=ALLOWED
    )
    assert issue is not None
    assert issue[0] == "prohibited_statement"
    assert issue[2] == 3


def test_at_most_32_statements():
    assert validate_read_only_script(";".join(["SELECT 1"] * 32), allowed_schemas=ALLOWED) is None
    issue = validate_read_only_script(";".join(["SELECT 1"] * 33), allowed_schemas=ALLOWED)
    assert issue is not None
    assert issue[0] == "too_many_statements"


# --------------------------------------------------------------------------
# Legacy behavior is byte-identical when the flag is off
# --------------------------------------------------------------------------

@pytest.mark.parametrize("sql,expected", [
    ("SELECT 1", None),
    ("INSERT INTO t VALUES (1)", ("not_a_select", "Only a single read-only SELECT query is allowed in the sandbox")),
    ("SELECT 1; SELECT 2", ("multiple_statements", "Only a single SELECT statement is allowed")),
    ("SELECT * FROM pg_catalog.pg_class", ("forbidden_schema", "system catalogs are not accessible in the sandbox")),
])
def test_legacy_validator_unchanged(sql, expected):
    assert validate_learner_sql(sql) == expected
