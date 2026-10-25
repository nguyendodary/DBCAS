"""Sandbox safety validation tests — Task 3.2 (DBCAS-17).

Two layers are exercised:

* ``validate_learner_sql`` — the pure static gate (no container needed for the
  unit tests): single read-only SELECT-family statements only.
* ``SandboxRunner.execute`` — the same checks applied end-to-end on the real
  sandbox container, proving the parser layer rejects hostile input before a
  connection is opened and that role/transaction limits still back it up.
"""

import pytest

from app.services.sql_validator import validate_learner_sql


def check(sql: str) -> str | None:
    """Return the error_type or None when the statement is acceptable."""
    result = validate_learner_sql(sql)
    return result[0] if result else None


class TestValidatorAccepts:
    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM students",
            "SELECT s.name FROM students s WHERE s.gpa > 3.0",
            "SELECT a.*, b.course FROM a JOIN b ON a.id = b.id",
            "SELECT dept, count(*) FROM t GROUP BY dept HAVING count(*) > 2",
            "SELECT * FROM t WHERE x IN (SELECT x FROM u)",
            "SELECT name FROM t WHERE id = (SELECT max(id) FROM t)",
            "WITH cte AS (SELECT 1 AS n) SELECT * FROM cte",
            "SELECT n, row_number() OVER (ORDER BY n) FROM t",
            "SELECT a FROM t UNION ALL SELECT a FROM u",
            "SELECT a FROM t INTERSECT SELECT a FROM u",
            "SELECT DISTINCT name FROM t ORDER BY name LIMIT 10",
            "SELECT * FROM public.students",
            "SELECT * FROM ds_abc123def456.students",
            "  -- leading comment\n  SELECT 1",
            "SELECT /* inline ; comment */ 1",
            "VALUES (1, 'a'), (2, 'b')",
            "(SELECT 1)",
        ],
    )
    def test_allowed(self, sql):
        allowed = {"ds_abc123def456"} if "ds_abc123def456" in sql else frozenset()
        assert validate_learner_sql(sql, allowed_schemas=allowed) is None


class TestValidatorRejects:
    @pytest.mark.parametrize(
        "sql",
        [
            "INSERT INTO t VALUES (1)",
            "UPDATE t SET a = 1",
            "DELETE FROM t",
            "DROP TABLE t",
            "ALTER TABLE t ADD COLUMN x int",
            "TRUNCATE t",
            "CREATE TABLE x (a int)",
            "CREATE INDEX i ON t (a)",
            "GRANT SELECT ON t TO someone",
            "REVOKE SELECT ON t FROM someone",
            "SELECT * INTO backup FROM t",
            "SELECT * FROM t FOR UPDATE",
            "SELECT * FROM t FOR SHARE",
            "EXPLAIN SELECT 1",
            "EXPLAIN ANALYZE SELECT 1",
            "SET statement_timeout = 0",
            "BEGIN",
            "COMMIT",
            "COPY t TO '/tmp/out'",
            "VACUUM t",
            "CALL do_thing()",
            "DO $$ BEGIN END $$",
            "LISTEN chan",
            "PREPARE q AS SELECT 1",
        ],
    )
    def test_statement_kind(self, sql):
        assert check(sql) in ("not_a_select", "prohibited_statement")

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT 1; SELECT 2",
            "SELECT 1; DROP TABLE t",
            "BEGIN; SELECT 1",
            "SELECT 1;\n-- hidden second\nSELECT 2",
            "SELECT 1 ; ; SELECT 2",
            "SELECT * FROM t; SELECT pg_sleep(60)",
        ],
    )
    def test_multiple_statements(self, sql):
        assert check(sql) == "multiple_statements"

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM pg_catalog.pg_authid",
            "SELECT * FROM pg_catalog.pg_shadow",
            "SELECT * FROM information_schema.tables",
            "SELECT * FROM pg_stat_activity",
            "SELECT * FROM pg_tables",
            "SELECT * FROM pg_toast.t",
            "SELECT datname FROM pg_catalog.pg_database",
            "SELECT * FROM otherdb.public.t",
            "SELECT * FROM mysql.users",
        ],
    )
    def test_forbidden_schema(self, sql):
        assert check(sql) == "forbidden_schema"

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT pg_sleep(10)",
            "SELECT pg_catalog.pg_sleep(1)",
            "SELECT set_config('statement_timeout', '0', false)",
            "SELECT current_setting('data_directory')",
            "SELECT inet_server_addr()",
            "SELECT dblink('host=dbcas-db', 'SELECT 1')",
            "SELECT lo_import('/etc/passwd')",
            "SELECT pg_read_file('/etc/passwd')",
            "SELECT pg_ls_dir('.')",
            "SELECT nextval('s')",
            "SELECT setval('s', 1)",
            "SELECT pg_terminate_backend(1)",
            "SELECT pg_notify('c', 'p')",
        ],
    )
    def test_unsafe_function(self, sql):
        assert check(sql) == "unsafe_function"

    @pytest.mark.parametrize(
        "sql",
        [
            "SELEC * FORM t",
            "SELECT * FROM",
            "SELECT (",
            "SEL\x00ECT 1",
            "SELECT 1\x07",
        ],
    )
    def test_malformed(self, sql):
        # Lenient parses land on not_a_select/prohibited; exact classification
        # matters less than rejection.
        assert check(sql) in (
            "syntax_error",
            "invalid_input",
            "not_a_select",
            "prohibited_statement",
        )

    def test_comment_only(self):
        assert check("-- just a comment") == "empty_query"
        assert check("/* nothing */") == "empty_query"

    def test_cte_with_embedded_delete(self):
        assert check(
            "WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x"
        ) == "prohibited_statement"

    def test_cte_with_embedded_insert(self):
        assert check(
            "WITH x AS (INSERT INTO t VALUES (1) RETURNING *) SELECT * FROM x"
        ) == "prohibited_statement"


SETUP_SQL = """
CREATE TABLE accounts (
    account_id INT PRIMARY KEY,
    owner VARCHAR(50) NOT NULL,
    balance NUMERIC(10,2) NOT NULL
);
INSERT INTO accounts VALUES (1, 'Ana', 100.00), (2, 'Bao', 250.50), (3, 'Chi', 0.00);
"""


@pytest.fixture()
def dataset(sandbox_runner):
    schema = sandbox_runner.provision_dataset(SETUP_SQL)
    yield schema
    # fixture-level cleanup handled by sandbox_runner's cleanup_datasets


class TestEndToEndSafety:
    """The validator runs inside execute(); the read-only role + rolled-back
    transaction back it up. These run on the real sandbox container."""

    def test_allowed_scopes_run(self, sandbox_runner, dataset):
        for sql in (
            "SELECT count(*) FROM accounts",
            "SELECT accounts.owner, accounts.balance FROM accounts JOIN accounts a2 USING (account_id)",
            "SELECT owner FROM accounts GROUP BY owner HAVING count(*) >= 1",
            "SELECT * FROM accounts WHERE balance > (SELECT avg(balance) FROM accounts)",
            "WITH big AS (SELECT * FROM accounts WHERE balance > 50) SELECT * FROM big",
        ):
            r = sandbox_runner.execute(sql, schema=dataset)
            assert r.success, f"{sql!r} -> {r.error_type} {r.error_message}"

    @pytest.mark.parametrize(
        "sql",
        [
            "INSERT INTO accounts VALUES (9, 'x', 1)",
            "UPDATE accounts SET balance = 0",
            "DELETE FROM accounts",
            "DROP TABLE accounts",
            "ALTER TABLE accounts ADD c int",
            "TRUNCATE accounts",
            "CREATE TABLE evil (a int)",
            "GRANT SELECT ON accounts TO learner_ro",
            "SELECT * FROM accounts FOR UPDATE",
            "SELECT 1; SELECT 2",
            "SELECT 1; DELETE FROM accounts",
            "SELECT pg_sleep(30)",
            "SELECT * FROM pg_catalog.pg_authid",
            "SELEC BAD SQL",
        ],
    )
    def test_rejected_before_execution(self, sandbox_runner, dataset, sql):
        r = sandbox_runner.execute(sql, schema=dataset)
        assert r.success is False
        assert r.error_type in (
            "not_a_select",
            "prohibited_statement",
            "multiple_statements",
            "unsafe_function",
            "forbidden_schema",
            "syntax_error",
        ), f"{sql!r} -> {r.error_type}"
        assert r.error_message

    def test_prohibited_errors_are_learner_safe(self, sandbox_runner, dataset):
        r = sandbox_runner.execute(
            "SELECT * FROM pg_catalog.pg_authid", schema=dataset
        )
        blob = f"{r.error_type} {r.error_message}"
        for token in ("learner_ro_dev", "password", "543", "/var/lib", "Traceback"):
            assert token not in blob

    def test_dataset_survives_hostile_attempts(self, sandbox_runner, dataset):
        for sql in (
            "DELETE FROM accounts",
            "DROP TABLE accounts",
            "UPDATE accounts SET balance = 9999",
        ):
            sandbox_runner.execute(sql, schema=dataset)
        r = sandbox_runner.execute(
            "SELECT count(*) FROM accounts", schema=dataset
        )
        assert r.success and r.rows == [[3]]
