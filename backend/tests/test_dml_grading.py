"""Writable demo sandbox: DML answers are graded by table state."""
from decimal import Decimal
from types import SimpleNamespace

from app.config import get_settings
from app.services.sandbox_runner import SandboxRunner
from app.services.sql_grading import grade_sql


def _runner():
    settings = get_settings().model_copy(update={"sandbox_writable": True})
    return SandboxRunner(settings)


def _dataset(expected, *, edge=False):
    return SimpleNamespace(
        dataset_name="regular" if not edge else "edge",
        setup_sql=(
            "CREATE TABLE dml_items(id INT PRIMARY KEY, name TEXT NOT NULL); "
            "INSERT INTO dml_items VALUES (1,'alpha'),(2,'beta'),(3,'gamma');"
        ),
        expected_result=expected,
        is_edge_case=edge,
    )


def test_ai_dml_reference_is_executed_before_serving():
    from app.services.practice_generation import validate_generated

    runner = _runner()
    concept = SimpleNamespace(concept_id=1, concept_code="PG-DML", concept_name="PG-DML")
    payload = SimpleNamespace(question_count=1, difficulties=["MEDIUM"], concept_ids=[1], source="ai")
    raw = {"questions": [{
        "concept_ids": [1],
        "difficulty_level": 3,
        "question_type": "sql",
        "prompt": "Ch\u1ebfn m\u1ed9t d\u00f2ng v\u00e0o b\u1ea3ng dml_items.",
        "explanation": "Gi\u1ea3i th\u00edch h\u1ee3p l\u1ec7 b\u1eb1ng ti\u1ebfng Vi\u1ec7t cho c\u00e2u h\u1ecfi n\u00e0y.",
        "source_refs": ["https://www.postgresql.org/docs/18/sql-insert.html"],
        "reference_answer": "INSERT INTO dml_items VALUES (1,'alpha');",
        "points": 1,
        "options": [],
        "setup_sql": "CREATE TABLE dml_items(id INT PRIMARY KEY, name TEXT);",
        "edge_setup_sql": "CREATE TABLE dml_items(id INT PRIMARY KEY, name TEXT);",
        "tables": ["dml_items"],
        "rubrics": [],
    }]}
    validated = validate_generated(raw, [concept], payload, runner,
                                   allowed_types={"sql"}, expected_types={"sql": 1},
                                   original_locale="vi")
    assert validated[0]["_datasets"][0]["expected_result"]["tables"][0]["rows"] == [[1, "alpha"]]


def test_writable_runner_captures_table_state_before_rollback():
    runner = _runner()
    schema = runner.provision_dataset(
        "CREATE TABLE dml_items(id INT PRIMARY KEY, name TEXT NOT NULL); "
        "INSERT INTO dml_items VALUES (1,'alpha'),(2,'beta');"
    )
    try:
        result = runner.execute_writable_script(
            "UPDATE dml_items SET name='gamma' WHERE id=2;",
            schema=schema,
            capture_tables=["dml_items"],
        )
    finally:
        runner.drop_dataset(schema)
    assert result.success and result.rolled_back
    assert result.table_states == [{
        "table": "dml_items",
        "columns": ["id", "name"],
        "rows": [[1, "alpha"], [2, "gamma"]],
    }]


def test_dml_grading_compares_the_resulting_table_state():
    runner = _runner()
    expected = {"tables": [{
        "table": "dml_items",
        "columns": ["id", "name"],
        "rows": [[1, "alpha"], [2, "gamma"], [3, "gamma"]],
    }], "ordered": False}
    question = SimpleNamespace(points=Decimal("5.00"))
    correct = grade_sql(
        question, [_dataset(expected)],
        [], "UPDATE dml_items SET name='gamma' WHERE id IN (2,3);", runner,
    )
    assert correct["score"] == Decimal("5.00")
    assert correct["grading_detail"]["grader"] == "sql_semantic"
    assert correct["grading_detail"]["datasets"][0]["mode"] == "state"

    wrong = grade_sql(
        question, [_dataset(expected)],
        [], "UPDATE dml_items SET name='wrong' WHERE id=2;", runner,
    )
    assert wrong["score"] == Decimal("0.00")
    assert wrong["grading_detail"]["datasets"][0]["status"] == "failed"


def test_dml_bank_pack_fixtures_execute_in_the_writable_sandbox():
    import json
    from app.config import ROOT_DIR
    from app.services.question_validator import question_problems

    runner = _runner()
    pack = json.loads((ROOT_DIR / "db" / "dml_practice_pack.json").read_text(encoding="utf-8"))
    known = {code for question in pack["questions"] for code in question["concept_codes"]}
    for question in pack["questions"]:
        problems = question_problems(question, known_concepts=known, runner=runner)
        assert problems == [], (question["key"], problems)
