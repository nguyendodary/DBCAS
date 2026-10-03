"""SQL answer verification & scoring tests — Task 3.3 (DBCAS-18).

The grader provisions every sql_test_dataset of the question (regular first,
edge cases after), runs the learner statement read-only in the sandbox, and
compares results *semantically* — equivalent SQL earns full credit, SQL text
is never compared. Evidence lands in attempt.grading_detail without leaking
expected rows or setup SQL.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models import (
    Account,
    Assessment,
    AssessmentSession,
    Attempt,
    Concept,
    Question,
    QuestionConcept,
    SqlTestDataset,
)
from app.services import sql_grading, sql_result
from app.services.sql_features import check_required, detect_features

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

# Edge case: an empty students table — correct SQL must still return the
# right shape (zero rows).
EDGE_SETUP_SQL = """
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    gpa NUMERIC(3,2)
);
"""

EXPECTED_NAMES = {"columns": ["name"], "rows": [["Ana"], ["Bao"], ["Chi"]]}
EXPECTED_NAMES_EDGE = {"columns": ["name"], "rows": []}


def _question(points="4.0"):
    return Question(
        question_type="sql",
        prompt="List all student names",
        reference_answer="SELECT name FROM students",
        points=Decimal(points),
    )


def _datasets():
    return [
        SqlTestDataset(
            dataset_name="base",
            setup_sql=SETUP_SQL,
            expected_result=EXPECTED_NAMES,
        ),
        SqlTestDataset(
            dataset_name="empty_edge",
            setup_sql=EDGE_SETUP_SQL,
            expected_result=EXPECTED_NAMES_EDGE,
            is_edge_case=True,
        ),
    ]


def _grade(sandbox_runner, sql, required=(), points="4.0"):
    return sql_grading.grade_sql(
        _question(points), _datasets(), list(required), sql, sandbox_runner
    )


class TestResultComparison:
    """Pure semantic comparison — no container needed."""

    def test_value_normalization_numeric(self):
        # JSON numbers & Decimals compare by value, not scale: 1 == 1.00.
        exp = sql_result.parse_expected({"rows": [[1, 1.50, True, None]]})
        out = sql_result.compare(
            ["a", "b", "c", "d"],
            [[Decimal("1.00"), Decimal("1.5"), True, None]],
            exp,
        )
        assert out.status == "passed"

    def test_string_number_does_not_equal_number(self):
        exp = sql_result.parse_expected({"rows": [["1.50"]]})
        out = sql_result.compare(["a"], [[Decimal("1.5")]], exp)
        assert out.status == "failed"

    def test_row_order_insensitive_by_default(self):
        exp = sql_result.parse_expected(EXPECTED_NAMES)
        out = sql_result.compare(["name"], [["Chi"], ["Ana"], ["Bao"]], exp)
        assert out.status == "passed"

    def test_row_order_sensitive_when_flagged(self):
        exp = sql_result.parse_expected({**EXPECTED_NAMES, "ordered": True})
        out = sql_result.compare(["name"], [["Bao"], ["Ana"], ["Chi"]], exp)
        assert out.status == "failed" and "rows" in out.failed

    def test_duplicate_multiplicity_matters(self):
        exp = sql_result.parse_expected({"rows": [["x"], ["x"]]})
        assert sql_result.compare(["a"], [["x"]], exp).status == "failed"
        assert (
            sql_result.compare(["a"], [["x"], ["x"], ["x"]], exp).status
            == "failed"
        )
        assert sql_result.compare(["a"], [["x"], ["x"]], exp).status == "passed"

    def test_null_semantics(self):
        exp = sql_result.parse_expected({"rows": [[None, "a"]]})
        assert (
            sql_result.compare(["a", "b"], [[None, "a"]], exp).status
            == "passed"
        )
        assert (
            sql_result.compare(["a", "b"], [["", "a"]], exp).status == "failed"
        )

    def test_column_name_set_comparison(self):
        # check_columns: names enforced as a set; rows realign by name.
        exp = sql_result.parse_expected(
            {
                "columns": ["Name", "GPA"],
                "rows": [["Ana", 3.5]],
                "check_columns": True,
            }
        )
        assert (
            sql_result.compare(["gpa", "name"], [[3.5, "Ana"]], exp).status
            == "passed"
        )
        assert (
            sql_result.compare(["student_name"], [["Ana"]], exp).status
            == "failed"
        )

    def test_column_alias_ok_without_check_columns(self):
        exp = sql_result.parse_expected(
            {"columns": ["name"], "rows": [["Ana"]]}
        )
        assert (
            sql_result.compare(["student_name"], [["Ana"]], exp).status
            == "passed"
        )

    def test_empty_expected(self):
        exp = sql_result.parse_expected({"columns": ["n"], "rows": []})
        assert sql_result.compare(["n"], [], exp).status == "passed"
        assert sql_result.compare(["n"], [[1]], exp).status == "failed"

    def test_unusable_expected(self):
        assert sql_result.parse_expected("not a dict") is None
        assert sql_result.parse_expected({"columns": ["a"]}) is None


class TestConceptFeatures:
    def test_detect(self):
        f = detect_features(
            "SELECT s.name, count(*) FROM students s "
            "JOIN enrollments e ON s.student_id = e.student_id "
            "WHERE gpa > 2 GROUP BY s.name HAVING count(*) > 1 "
            "ORDER BY s.name LIMIT 5"
        )
        assert {
            "select",
            "join",
            "where",
            "group_by",
            "having",
            "aggregate",
            "order_by",
            "limit",
        } <= f

    def test_subquery_and_cte(self):
        assert "subquery" in detect_features(
            "SELECT * FROM t WHERE x IN (SELECT x FROM u)"
        )
        assert "cte" in detect_features("WITH w AS (SELECT 1) SELECT * FROM w")

    def test_union_is_not_subquery(self):
        f = detect_features("SELECT a FROM t UNION SELECT a FROM u")
        assert "subquery" not in f and "set_operation" in f

    def test_check_required(self):
        missing, unverified = check_required(
            "SELECT a FROM t JOIN u ON t.id = u.id", ["Joins", "Group By"]
        )
        assert missing == ["Group By"] and unverified == []

    def test_unmapped_concept_unverified(self):
        missing, unverified = check_required("SELECT 1", ["Temporal Tables"])
        assert missing == [] and unverified == ["Temporal Tables"]


class TestServiceGrading:
    """grade_sql() against the real sandbox; in-memory question/datasets."""

    def test_exact_correct(self, sandbox_runner):
        r = _grade(sandbox_runner, "SELECT name FROM students")
        assert r["is_correct"] is True
        assert r["score"] == Decimal("4.00")

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT s.name FROM students s ORDER BY s.name",
            "SELECT name AS student_name FROM students",
            "SELECT DISTINCT name FROM students",
            "SELECT name FROM students WHERE name IS NOT NULL",
            "WITH w AS (SELECT name FROM students) SELECT name FROM w",
        ],
    )
    def test_equivalent_sql_full_credit(self, sandbox_runner, sql):
        # (name IS NOT NULL keeps all three students — Chi's NULL is in gpa)
        r = _grade(sandbox_runner, sql)
        assert r["is_correct"] is True, (sql, r["grading_detail"])
        assert r["score"] == Decimal("4.00")

    def test_wrong_rows_partial(self, sandbox_runner):
        # Fails the base dataset but legitimately returns the empty result the
        # edge dataset expects — 1/2 datasets -> half credit.
        r = _grade(sandbox_runner, "SELECT name FROM students WHERE gpa > 3.2")
        assert r["score"] == Decimal("2.00") and r["is_correct"] is False
        statuses = {d["dataset"]: d["status"] for d in r["grading_detail"]["datasets"]}
        assert statuses == {"base": "failed", "empty_edge": "passed"}

    def test_partial_credit_edge_only(self, sandbox_runner):
        # Same split via a different predicate: drops Chi on base, empty is
        # correct on the edge dataset.
        r = _grade(
            sandbox_runner, "SELECT name FROM students WHERE gpa IS NOT NULL"
        )
        assert r["score"] == Decimal("2.00")
        assert r["grading_detail"]["datasets_passed"] == 1

    def test_wrong_rows_zero(self, sandbox_runner):
        # Wrong on every dataset: returns a row even on the empty edge case.
        r = _grade(sandbox_runner, "SELECT 42")
        assert r["score"] == Decimal("0")
        assert r["is_correct"] is False

    def test_syntax_error(self, sandbox_runner):
        r = _grade(sandbox_runner, "SELEC name FORM students")
        assert r["score"] == Decimal("0")
        assert r["grading_detail"]["status"] == "error"
        assert r["grading_detail"]["datasets"][0]["error_type"] is not None

    def test_prohibited_sql(self, sandbox_runner):
        r = _grade(sandbox_runner, "SELECT 1; DROP TABLE students")
        assert r["score"] == Decimal("0")
        assert r["grading_detail"]["status"] == "error"

    def test_timeout_scores_zero(self, sandbox_runner):
        r = _grade(
            sandbox_runner,
            "SELECT count(*) FROM generate_series(1, 100000) a "
            "CROSS JOIN generate_series(1, 100000) b",
        )
        assert r["score"] == Decimal("0")
        assert (
            r["grading_detail"]["datasets"][0]["error_type"] == "timeout"
        )

    def test_required_concept_missing(self, sandbox_runner):
        r = _grade(
            sandbox_runner,
            "SELECT name FROM students",
            required=["Joins"],
        )
        assert r["score"] == Decimal("0")
        assert r["grading_detail"]["missing_required_concepts"] == ["Joins"]

    def test_required_concept_present(self, sandbox_runner):
        ds = [
            SqlTestDataset(
                dataset_name="base",
                setup_sql=SETUP_SQL,
                expected_result={
                    "columns": ["name"],
                    "rows": [["Ana"], ["Bao"]],
                },
            )
        ]
        r = sql_grading.grade_sql(
            _question(),
            ds,
            ["Joins"],
            "SELECT s.name FROM students s "
            "JOIN enrollments e ON s.student_id = e.student_id "
            "GROUP BY s.name",
            sandbox_runner,
        )
        assert r["is_correct"] is True


def _learner_token(client, email="scorer@test.dev"):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Scorer",
            "email": email,
            "password": "Secret123!",
            "password_confirm": "Secret123!",
        },
    )
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Secret123!"},
    ).json()["access_token"]


@pytest.fixture()
def served_sql_q(db_session, client):
    """Live session serving a 2-dataset (regular + edge) SQL question."""
    token = _learner_token(client)
    learner = db_session.query(Account).filter_by(email="scorer@test.dev").one()
    assessment = Assessment(
        title="SQL scoring", status="active", created_by=learner.account_id
    )
    question = Question(
        question_type="sql",
        prompt="List all student names",
        reference_answer="SELECT name FROM students",
        difficulty_level=1,
        points=Decimal("4.0"),
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
    db_session.add_all(
        [
            SqlTestDataset(
                question=question,
                dataset_name="base",
                setup_sql=SETUP_SQL,
                expected_result=EXPECTED_NAMES,
            ),
            SqlTestDataset(
                question=question,
                dataset_name="empty_edge",
                setup_sql=EDGE_SETUP_SQL,
                expected_result=EXPECTED_NAMES_EDGE,
                is_edge_case=True,
            ),
            attempt,
        ]
    )
    db_session.commit()
    return {
        "token": token,
        "session_id": session.session_id,
        "question_id": question.question_id,
        "attempt_id": attempt.attempt_id,
    }


def _submit(client, served, sql):
    payload = {"question_id": served["question_id"]}
    if sql is not None:
        payload["sql_answer"] = sql
    return client.post(
        f"/api/v1/sessions/{served['session_id']}/answers",
        headers={"Authorization": f"Bearer {served['token']}"},
        json=payload,
    )


class TestEndpointGrading:
    def test_correct_full_credit(self, client, served_sql_q):
        r = _submit(client, served_sql_q, "SELECT name FROM students")
        assert r.status_code == 200
        body = r.json()
        assert body["is_correct"] is True
        assert Decimal(body["score"]) == Decimal("4.0")

    def test_equivalent_alias_scores(self, client, served_sql_q):
        r = _submit(
            client, served_sql_q, "SELECT s.name FROM students AS s"
        )
        assert r.status_code == 200 and r.json()["is_correct"] is True

    def test_wrong_result_zero(self, client, served_sql_q):
        r = _submit(client, served_sql_q, "SELECT 42")
        body = r.json()
        assert r.status_code == 200
        assert body["is_correct"] is False
        assert Decimal(body["score"]) == Decimal("0")

    def test_syntax_error_scores_zero(self, client, served_sql_q):
        r = _submit(client, served_sql_q, "SELEC name FORM students")
        assert r.status_code == 200
        assert Decimal(r.json()["score"]) == Decimal("0")

    def test_prohibited_sql_scores_zero(self, client, served_sql_q):
        r = _submit(client, served_sql_q, "SELECT 1; DROP TABLE students")
        assert r.status_code == 200
        assert Decimal(r.json()["score"]) == Decimal("0")

    def test_empty_answer_rejected(self, client, served_sql_q):
        assert _submit(client, served_sql_q, "   ").status_code == 422
        assert _submit(client, served_sql_q, None).status_code == 422

    def test_persistence_and_evidence(self, client, served_sql_q, db_session):
        r = _submit(client, served_sql_q, "SELECT name FROM students")
        assert r.status_code == 200
        attempt = (
            db_session.query(Attempt)
            .filter_by(attempt_id=served_sql_q["attempt_id"])
            .one()
        )
        assert attempt.sql_answer == "SELECT name FROM students"
        assert attempt.submitted_at is not None
        assert attempt.score == Decimal("4.00")
        detail = attempt.grading_detail
        assert detail["grader"] == "sql_semantic"
        assert detail["datasets_total"] == 2
        assert detail["datasets_passed"] == 2
        statuses = {d["dataset"]: d["status"] for d in detail["datasets"]}
        assert statuses == {"base": "passed", "empty_edge": "passed"}
        # hidden data must not leak into evidence
        assert "expected_result" not in str(detail)
        assert "setup_sql" not in str(detail)

    def test_required_concept_endpoint(
        self, client, served_sql_q, db_session
    ):
        concept = Concept(
            concept_code="JOIN", concept_name="Joins", subject_area="SQL"
        )
        db_session.add(concept)
        db_session.flush()
        db_session.add(
            QuestionConcept(
                question_id=served_sql_q["question_id"],
                concept_id=concept.concept_id,
                is_required=True,
            )
        )
        db_session.commit()
        r = _submit(client, served_sql_q, "SELECT name FROM students")
        assert Decimal(r.json()["score"]) == Decimal("0")
        attempt = (
            db_session.query(Attempt)
            .filter_by(attempt_id=served_sql_q["attempt_id"])
            .one()
        )
        assert attempt.grading_detail["missing_required_concepts"] == ["Joins"]

    def test_double_submit_conflict(self, client, served_sql_q):
        _submit(client, served_sql_q, "SELECT name FROM students")
        r = _submit(client, served_sql_q, "SELECT name FROM students")
        assert r.status_code == 409
