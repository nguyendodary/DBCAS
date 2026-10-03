"""SQL sandbox runner tests — Task 3.1 (DBCAS-16).

Runs against the real sandbox image (sandbox/Dockerfile + learner_ro init) in
a disposable container alongside the system test database. Verifies the UC13 /
QA03 contract: SELECT executes inside a rolled-back read-only transaction on a
provisioned dataset schema; writes, timeouts, and malformed SQL come back as
classified errors without leaking server internals.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.config import get_settings
from app.models import (
    Assessment,
    AssessmentSession,
    Attempt,
    Question,
    SqlTestDataset,
)

SETUP_SQL = """
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    gpa NUMERIC(3,2)
);
CREATE TABLE enrollments (
    student_id INT NOT NULL REFERENCES students(student_id),
    course VARCHAR(20) NOT NULL
);
INSERT INTO students VALUES (1, 'Ana', 3.50), (2, 'Bao', 3.10), (3, 'Chi', NULL);
INSERT INTO enrollments VALUES (1, 'DB101'), (1, 'DB102'), (2, 'DB101');
"""


@pytest.fixture()
def dataset(sandbox_runner):
    schema = sandbox_runner.provision_dataset(SETUP_SQL)
    yield schema


class TestEnvironment:
    def test_health_check(self, sandbox_runner):
        assert sandbox_runner.health_check() is True

    def test_validate_environment_clean(self, sandbox_runner):
        # Covers: learner role present, not superuser, timeout effective,
        # admin connection works, server is PostgreSQL 17.
        assert sandbox_runner.validate_environment() == []


class TestExecution:
    def test_select_rows_and_columns(self, sandbox_runner, dataset):
        r = sandbox_runner.execute(
            "SELECT student_id, name FROM students ORDER BY student_id",
            schema=dataset,
        )
        assert r.success is True
        assert r.columns == ["student_id", "name"]
        assert r.rows == [[1, "Ana"], [2, "Bao"], [3, "Chi"]]
        assert r.row_count == 3
        assert r.error_type is None

    def test_join_group_by(self, sandbox_runner, dataset):
        r = sandbox_runner.execute(
            "SELECT s.name, count(*) AS n FROM students s "
            "JOIN enrollments e ON e.student_id = s.student_id "
            "GROUP BY s.name ORDER BY n DESC",
            schema=dataset,
        )
        assert r.success is True
        assert r.row_count == 2

    def test_null_and_numeric_values(self, sandbox_runner, dataset):
        r = sandbox_runner.execute(
            "SELECT gpa FROM students WHERE student_id = 3", schema=dataset
        )
        assert r.success and r.rows == [[None]]

    def test_write_blocked_by_readonly_role(self, sandbox_runner, dataset):
        r = sandbox_runner.execute(
            "INSERT INTO students VALUES (9, 'Eve', 4.0)", schema=dataset
        )
        assert r.success is False
        assert r.error_type == "prohibited_statement"

    def test_schema_mutation_blocked(self, sandbox_runner, dataset):
        r = sandbox_runner.execute("DROP TABLE students", schema=dataset)
        assert r.success is False
        assert r.error_type == "prohibited_statement"

    def test_malformed_sql(self, sandbox_runner, dataset):
        r = sandbox_runner.execute("SELEC * FORM students", schema=dataset)
        assert r.success is False
        assert r.error_type == "syntax_error"

    def test_undefined_table(self, sandbox_runner, dataset):
        r = sandbox_runner.execute("SELECT * FROM nope", schema=dataset)
        assert r.success is False
        assert r.error_type == "schema_error"

    def test_statement_timeout(self, sandbox_runner, dataset):
        r = sandbox_runner.execute("SELECT pg_sleep(10)", schema=dataset)
        assert r.success is False
        assert r.error_type == "timeout"
        # 3 s statement timeout — well under the role budget + overhead.
        assert r.execution_time_ms < 8000

    def test_empty_query(self, sandbox_runner):
        r = sandbox_runner.execute("   ")
        assert r.success is False and r.error_type == "empty_query"

    def test_oversized_query(self, sandbox_runner):
        limit = get_settings().sandbox_max_sql_bytes
        r = sandbox_runner.execute("SELECT " + "1," * limit + "1")
        assert r.success is False and r.error_type == "query_too_large"

    def test_result_row_cap(self, sandbox_runner, dataset):
        limit = get_settings().sandbox_max_rows
        r = sandbox_runner.execute(
            f"SELECT generate_series(1, {limit + 10})", schema=dataset
        )
        assert r.success is False and r.error_type == "result_too_large"

    def test_error_messages_do_not_leak_internals(self, sandbox_runner, dataset):
        r = sandbox_runner.execute("DROP TABLE students", schema=dataset)
        blob = f"{r.error_type} {r.error_message}"
        for token in ("learner_ro_dev", "5432", "/var/lib", "psycopg", "docker"):
            assert token not in blob


class TestIsolation:
    def test_dataset_not_visible_outside_schema(self, sandbox_runner, dataset):
        r = sandbox_runner.execute("SELECT * FROM students")
        assert r.success is False  # not on search_path without the schema

    def test_executions_do_not_leak_state(self, sandbox_runner):
        s1 = sandbox_runner.provision_dataset(
            "CREATE TABLE only_here (id INT); INSERT INTO only_here VALUES (1);"
        )
        try:
            r = sandbox_runner.execute("SELECT count(*) FROM only_here", schema=s1)
            assert r.success and r.rows == [[1]]
        finally:
            sandbox_runner.drop_dataset(s1)
        s2 = sandbox_runner.provision_dataset(
            "CREATE TABLE other_table (id INT);"
        )
        try:
            r = sandbox_runner.execute(
                "SELECT count(*) FROM only_here", schema=s2
            )
            assert r.success is False  # previous dataset is gone
            r = sandbox_runner.execute(
                "SELECT count(*) FROM other_table", schema=s2
            )
            assert r.success and r.rows == [[0]]
        finally:
            sandbox_runner.drop_dataset(s2)

    def test_rollback_between_executions(self, sandbox_runner, dataset):
        # Even a failed/rolled-back attempt must not change the dataset.
        sandbox_runner.execute(
            "DELETE FROM students", schema=dataset
        )  # blocked + rolled back
        r = sandbox_runner.execute(
            "SELECT count(*) FROM students", schema=dataset
        )
        assert r.success and r.rows == [[3]]

    def test_provision_failure_raises_sandbox_error(self, sandbox_runner):
        from app.services.sandbox_runner import SandboxError

        with pytest.raises(SandboxError) as exc:
            sandbox_runner.provision_dataset("CREATE TABLE broken (")
        assert exc.value.code == "dataset_setup_failed"


# ---------- HTTP surface: POST /api/v1/sessions/{id}/sql-run ----------


def _learner_token(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Sql Learner",
            "email": "sql-learner@test.dev",
            "password": "Secret123!",
            "password_confirm": "Secret123!",
        },
    )
    return client.post(
        "/api/v1/auth/login",
        json={"email": "sql-learner@test.dev", "password": "Secret123!"},
    ).json()["access_token"]


@pytest.fixture()
def served_sql(db_session, client):
    """A live session with a served SQL question + one configured dataset."""
    from app.models import Account

    token = _learner_token(client)
    learner = db_session.query(Account).filter_by(email="sql-learner@test.dev").one()
    assessment = Assessment(
        title="SQL A", status="active", created_by=learner.account_id
    )
    question = Question(
        question_type="sql",
        prompt="List student names",
        reference_answer="SELECT name FROM students",
        difficulty_level=1,
        points=Decimal("3.0"),
        status="validated",
        created_by=learner.account_id,
    )
    session = AssessmentSession(
        assessment=assessment,
        learner_id=learner.account_id,
        status="in_progress",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
    )
    attempt = Attempt(session=session, question=question, seq_no=1)
    dataset = SqlTestDataset(
        question=question,
        dataset_name="base",
        setup_sql=SETUP_SQL,
        expected_result={"columns": ["name"], "rows": [["Ana"], ["Bao"], ["Chi"]]},
    )
    db_session.add_all([question, session, attempt, dataset])
    db_session.commit()
    return {
        "token": token,
        "session_id": session.session_id,
        "question_id": question.question_id,
    }


def _run(client, served, sql, session_id=None, question_id=None):
    return client.post(
        f"/api/v1/sessions/{session_id or served['session_id']}/sql-run",
        headers={"Authorization": f"Bearer {served['token']}"},
        json={
            "question_id": question_id or served["question_id"],
            "sql": sql,
        },
    )


def test_sql_run_endpoint_success(client, served_sql):
    r = _run(client, served_sql, "SELECT name FROM students ORDER BY name")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["columns"] == ["name"]
    assert body["row_count"] == 3


def test_sql_run_endpoint_error_result(client, served_sql):
    r = _run(client, served_sql, "DELETE FROM students")
    assert r.status_code == 200  # sanitized failure is data, not an API error
    body = r.json()
    assert body["success"] is False
    assert body["error_type"] == "prohibited_statement"


def test_sql_run_requires_auth(client, served_sql):
    r = client.post(
        f"/api/v1/sessions/{served_sql['session_id']}/sql-run",
        json={"question_id": served_sql["question_id"], "sql": "SELECT 1"},
    )
    assert r.status_code == 401


def test_sql_run_wrong_session(client, served_sql):
    r = _run(client, served_sql, "SELECT 1", session_id=999999)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "session_not_found"


def test_sql_run_question_not_served(client, served_sql):
    r = _run(client, served_sql, "SELECT 1", question_id=999999)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "question_not_served"


def test_sql_run_non_sql_question(client, served_sql, db_session):
    from app.models import Account, McqOption

    learner = db_session.query(Account).filter_by(email="sql-learner@test.dev").one()
    mcq = Question(
        question_type="mcq", prompt="q", points=Decimal("1"),
        status="validated", created_by=learner.account_id,
    )
    mcq.options = [McqOption(option_label="A", option_text="x", is_correct=True)]
    attempt = Attempt(
        session_id=served_sql["session_id"], question=mcq, seq_no=2
    )
    db_session.add_all([mcq, attempt])
    db_session.commit()
    r = _run(client, served_sql, "SELECT 1", question_id=mcq.question_id)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unsupported_question_type"
