"""Whole corpus checks and executable regressions for reviewed content defects."""
from copy import deepcopy
import json

import pytest

from app.config import ROOT_DIR
from app.services.question_validator import bank_problems, fingerprint, question_problems, text_problems


def corpus():
    from app.validate_bank import load_corpus
    return load_corpus()


def question(key):
    return next(q for pack in corpus()[0] for q in pack["questions"] if q["key"] == key)


def valid_mcq():
    return {"key": "validator-mcq", "question_type": "mcq", "original_locale": "vi",
        "prompt": "Trong SELECT, thành phần nào quy định các cột đầu ra?",
        "explanation": "Danh sách biểu thức sau SELECT quy định các cột được trả về.",
        "source_refs": [{"url": "https://www.postgresql.org/docs/18/queries-select-lists.html"}],
        "concept_codes": ["SQL-SELECT"], "difficulty_level": 1, "points": 1,
        "options": [{"option_label": label, "option_text": text, "is_correct": index == 0}
            for index, (label, text) in enumerate(zip("ABCD", ["Danh sách SELECT", "WHERE", "ORDER BY", "HAVING"]))]}


def test_all_source_questions_pass_the_shared_validator():
    packs, translations = corpus()
    failures = bank_problems(packs, translations)
    assert not failures, json.dumps(failures, ensure_ascii=False, indent=2)


def test_every_source_sql_has_nonempty_primary_and_executes_repeatably(sandbox_runner):
    packs, translations = corpus()
    failures = {}
    for pack in packs:
        for q in pack["questions"]:
            if q["question_type"] == "sql":
                errors = question_problems(q, vietnamese=translations.get(q["key"]), runner=sandbox_runner)
                if errors:
                    failures[q["key"]] = errors
    assert not failures, failures


@pytest.mark.parametrize("change,expected", [
    ("missing_reference", "source_refs"), ("untrusted_reference", "source_refs"),
    ("obsolete_reference", "obsolete"), ("missing_explanation", "explanation"),
    ("multiple_answers", "exactly one"), ("duplicate_choices", "distinct"),
    ("wrong_type", "question_type"), ("bad_difficulty", "difficulty_level"),
    ("unknown_concept", "unknown classification"), ("duplicate_concept", "unique"),
    ("wrong_language", "Vietnamese"), ("mojibake", "encoding"),
    ("hidden_text", "hidden"), ("nonfinite", "finite"), ("type_fields", "incompatible"),
])
def test_common_validator_rejects_invalid_content(change, expected):
    q = valid_mcq()
    assert question_problems(q, known_concepts={"SQL-SELECT"}) == []
    if change == "missing_reference": q["source_refs"] = []
    elif change == "untrusted_reference": q["source_refs"][0]["url"] = "https://example.test/docs/18/select.html"
    elif change == "obsolete_reference": q["source_refs"][0]["url"] = "https://www.postgresql.org/docs/18/textsearch-types.html"
    elif change == "missing_explanation": q["explanation"] = ""
    elif change == "multiple_answers": q["options"][1]["is_correct"] = True
    elif change == "duplicate_choices": q["options"][1]["option_text"] = q["options"][0]["option_text"]
    elif change == "wrong_type": q["question_type"] = "video"
    elif change == "bad_difficulty": q["difficulty_level"] = True
    elif change == "unknown_concept": q["concept_codes"] = ["UNKNOWN"]
    elif change == "duplicate_concept": q["concept_codes"] *= 2
    elif change == "wrong_language": q["prompt"] = "Which clause filters the result rows?"
    elif change == "mojibake": q["prompt"] += " \ufffd"
    elif change == "hidden_text": q["prompt"] += "\u200b"
    elif change == "nonfinite": q["points"] = float("nan")
    elif change == "type_fields": q["datasets"] = [{"setup_sql": "CREATE TABLE t(id int)"}]
    assert any(expected in error for error in question_problems(q, known_concepts={"SQL-SELECT"}))


@pytest.mark.parametrize("duplicate", ["id", "prompt"])
def test_bank_validator_detects_global_duplicates(duplicate):
    first = valid_mcq()
    second = deepcopy(first)
    if duplicate == "id": second["prompt"] += " Hãy giải thích lựa chọn."
    else: second["key"] = "second"
    pack = {"concepts": [{"concept_code": "SQL-SELECT"}], "questions": [first, second]}
    vi = {q["key"]: {"prompt": q["prompt"], "explanation": q["explanation"],
          "option_texts": {o["option_label"]: o["option_text"] for o in q["options"]}} for q in (first, second)}
    assert any(("unique stable" if duplicate == "id" else "duplicate of") in error
               for errors in bank_problems([pack], vi).values() for error in errors)


def test_numbered_description_fillers_are_not_unique_questions():
    assert fingerprint("Chọn mô tả đúng. (Tình huống 1)") == fingerprint("Chọn mô tả đúng. (Tình huống 2)")


@pytest.mark.parametrize("text", ["CALL gọi procedure; SELECT gọi function.", "INSERT chèn bao nhiêu dòng?",
    "ALTER SYSTEM ghi cấu hình vào đâu?", "CASCADE xóa chuỗi quyền phụ thuộc.", "Dùng trigger cho mọi tình huống."])
def test_language_check_accepts_natural_technical_vietnamese(text):
    assert text_problems(text, "text", vietnamese=True) == []


def test_initials_reference_handles_one_many_and_repeated_space_words(sandbox_runner):
    schema = sandbox_runner.provision_dataset("CREATE TABLE customers(id int, name text); "
        "INSERT INTO customers VALUES (1,'alice'),(2,'amanda brown'),(3,'camila delgado evans'),(4,'  duong  van  an  ')")
    try:
        result = sandbox_runner.execute(question("pg-s053")["reference_answer"], schema=schema)
        assert result.success
        assert result.rows == [[1, "A"], [2, "A.B"], [3, "C.D.E"], [4, "D.V.A"]]
    finally:
        sandbox_runner.drop_dataset(schema)


def test_orphan_manager_reference_uses_employees_not_departments(sandbox_runner):
    schema = sandbox_runner.provision_dataset("CREATE TABLE employees(id int PRIMARY KEY, mgr_id int); "
        "CREATE TABLE departments(id int PRIMARY KEY); INSERT INTO departments VALUES(1),(99); "
        "INSERT INTO employees VALUES(1,NULL),(2,1),(3,99),(4,NULL)")
    try:
        result = sandbox_runner.execute(question("pg-s056")["reference_answer"], schema=schema)
        assert result.success and result.rows == [[3]]
    finally:
        sandbox_runner.drop_dataset(schema)


def test_empty_edge_results_are_rejected_by_the_shared_content_gate():
    q = deepcopy(question("pg-s001"))
    q["datasets"][1]["expected_result"]["rows"] = []
    assert any("nonempty" in error for error in question_problems(q))


@pytest.mark.parametrize("expression", ["current_schema()", "current_schemas(true)",
    "CURRENT_USER", "SESSION_USER", "CURRENT_ROLE", "USER", "current_database()",
    "version()", "LOCALTIME", "date_trunc('day', LOCALTIMESTAMP)"])
def test_sql_reference_cannot_depend_on_the_provisioning_environment(expression):
    q = deepcopy(question("pg-s001"))
    q["reference_answer"] = "SELECT " + expression
    assert any("environment-dependent" in error for error in question_problems(q))


def test_sql_reference_allows_context_names_inside_literals():
    q = deepcopy(question("pg-s001"))
    q["reference_answer"] = "SELECT 'current_schema() now() CURRENT_USER' AS example"
    assert not any("dependent" in error for error in question_problems(q))


def test_original_empty_input_sql_behavior_remains_covered_separately(sandbox_runner):
    historical = json.loads((ROOT_DIR / "db/reviewed_question_before.json").read_text(encoding="utf-8"))
    fixes = json.loads((ROOT_DIR / "db/reviewed_question_fixes.json").read_text(encoding="utf-8"))
    checked = 0
    for key, fix in fixes.items():
        if not fix.get("edge_setup_append"):
            continue
        q = historical[key]["question"]
        for dataset in q["datasets"]:
            if dataset["expected_result"]["rows"]:
                continue
            schema = sandbox_runner.provision_dataset(dataset["setup_sql"])
            try:
                result = sandbox_runner.execute(q["reference_answer"], schema=schema)
                assert result.success and result.rows == [], key
                checked += 1
            finally:
                sandbox_runner.drop_dataset(schema)
    assert checked == 30
