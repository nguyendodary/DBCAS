"""Step 3 — opt-in multi-statement READ-ONLY script execution.

Integration cases run against the real disposable sandbox container using
synthetic data only. The legacy single-statement path is proven unchanged.
"""

import pytest

from app.config import Settings, get_settings
from app.services.sandbox_runner import SandboxRunner
from app.services.sql_classifier import validate_writable_script

SETUP_SQL = """
CREATE TABLE t (id INT PRIMARY KEY, name TEXT);
INSERT INTO t VALUES (1, 'a'), (2, 'b'), (3, 'c');
"""


@pytest.fixture()
def dataset(sandbox_runner):
    schema = sandbox_runner.provision_dataset(SETUP_SQL)
    yield schema
    sandbox_runner.drop_dataset(schema)


def test_multi_select_per_statement_results(sandbox_runner, dataset):
    result = sandbox_runner.execute_script(
        "SELECT 1 AS one; SELECT id FROM t ORDER BY id; SELECT count(*) AS n FROM t",
        schema=dataset,
    )
    assert result.success is True
    assert result.error_type is None
    assert result.mode == "read_only"
    assert result.rolled_back is True
    assert len(result.statements) == 3
    assert [s["index"] for s in result.statements] == [1, 2, 3]
    assert result.statements[1]["rows"] == [[1], [2], [3]]
    # Top-level fields mirror the last row-returning statement for old clients.
    assert result.columns == ["n"]
    assert result.rows == [[3]]
    assert result.row_count == 1


def test_comments_and_dollar_quoting(sandbox_runner, dataset):
    result = sandbox_runner.execute_script(
        "-- first\nSELECT $$a;b$$ AS literal; /* second */ SELECT id FROM t LIMIT 1",
        schema=dataset,
    )
    assert result.success is True
    assert result.statements[0]["rows"] == [["a;b"]]
    assert result.statements[1]["rows"] == [[1]]


def test_error_reports_failing_statement_index(sandbox_runner, dataset):
    result = sandbox_runner.execute_script(
        "SELECT 1; SELECT * FROM table_that_does_not_exist; SELECT 3",
        schema=dataset,
    )
    assert result.success is False
    assert result.error_statement_index == 2
    assert result.statements[-1]["error_type"] == "schema_error"
    assert result.columns == []


def test_policy_rejection_before_connect(sandbox_runner, dataset):
    result = sandbox_runner.execute_script(
        "SELECT 1; INSERT INTO t VALUES (9, 'x'); SELECT 3", schema=dataset
    )
    assert result.success is False
    assert result.error_type == "prohibited_statement"
    assert result.error_statement_index == 2
    assert result.statements == []


def test_script_row_cap(sandbox_runner, dataset):
    settings = get_settings().model_copy(update={"sandbox_max_rows_per_script": 2})
    limited = SandboxRunner(settings)
    result = limited.execute_script(
        "SELECT id FROM t ORDER BY id; SELECT id FROM t ORDER BY id", schema=dataset
    )
    assert result.success is False
    assert result.error_type == "result_too_large"


def test_writable_ddl_dml_select_and_cleanup(sandbox_runner):
    settings = get_settings().model_copy(update={"sandbox_writable": True})
    writable = SandboxRunner(settings)
    schema = writable.provision_dataset(SETUP_SQL)
    try:
        result = writable.execute_writable_script(
            "CREATE TABLE demo_item(id INT PRIMARY KEY, name TEXT); "
            "INSERT INTO demo_item VALUES (1, 'alpha'), (2, 'beta'); "
            "SELECT id, name FROM demo_item ORDER BY id",
            schema=schema,
        )
        assert result.success is True, result.error_message
        assert result.mode == "writable" and result.rolled_back is True
        assert result.rows == [[1, "alpha"], [2, "beta"]]
        # The script transaction rolled back, so the table is gone.
        after = writable.execute("SELECT * FROM demo_item", schema=schema)
        assert after.success is False
        assert after.error_type in {"schema_error", "prohibited_statement"}
    finally:
        writable.drop_dataset(schema)


def test_legacy_single_statement_unchanged(sandbox_runner, dataset):
    legacy = sandbox_runner.execute("SELECT id FROM t ORDER BY id", schema=dataset)
    assert legacy.success is True
    assert legacy.columns == ["id"]
    assert legacy.rows == [[1], [2], [3]]
    assert legacy.statements == []
    assert legacy.error_statement_index is None
    write = sandbox_runner.execute("INSERT INTO t VALUES (9, 'x')", schema=dataset)
    assert write.error_type == "not_a_select"


# --------------------------------------------------------------------------
# Flags (all DEFAULT OFF) and fail-closed startup validation
# --------------------------------------------------------------------------

def test_flags_default_off():
    settings = Settings(_env_file=None)
    assert settings.sandbox_multi_statement is False
    assert settings.sandbox_writable is False
    assert settings.grading_state_mode is False


def test_writable_policy_allows_ddl_dml_and_select():
    assert validate_writable_script(
        "CREATE TABLE demo_t(id INT PRIMARY KEY, note TEXT); "
        "INSERT INTO demo_t VALUES (1, 'a'), (2, 'b'); "
        "UPDATE demo_t SET note='c' WHERE id=2; "
        "SELECT id, note FROM demo_t ORDER BY id"
    ) is None


@pytest.mark.parametrize("sql", [
    "GRANT SELECT ON demo_t TO learner_ro",
    "COPY demo_t FROM '/etc/passwd'",
    "DO $$ BEGIN PERFORM 1; END $$",
    "CREATE ROLE attacker",
    "CREATE EXTENSION dblink",
    "VACUUM demo_t",
])
def test_writable_policy_rejects_privilege_and_admin_statements(sql):
    issue = validate_writable_script(sql)
    assert issue is not None
    assert issue[0] == "prohibited_statement"


def test_writable_outside_development_requires_ephemeral():
    with pytest.raises(ValueError, match="SANDBOX_MODE=ephemeral"):
        Settings(
            _env_file=None,
            deployment_mode="staging",
            jwt_secret="A" * 40,
            database_url="postgresql://u:longpassword123456@db-host:5432/dbcas",
            sandbox_url="postgresql://learner_ro:longpassword123456@sandbox-host:5432/postgres",
            sandbox_admin_url="postgresql://postgres:longpassword123456@sandbox-host:5432/postgres",
            frontend_url="https://example.edu",
            cors_origins=["https://example.edu"],
            sandbox_writable=True,
            sandbox_mode="shared",
        )
