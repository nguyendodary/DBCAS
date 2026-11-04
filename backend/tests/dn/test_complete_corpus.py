"""Derived bank capacity, immutable answers, safe upgrades and idempotency."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import json

import pytest
from sqlalchemy import func, select

from app.benchmark import import_pack
from app.config import ROOT_DIR
from app.models import AssessmentSession, Attempt, Question, SystemSetting
from app.repositories import AssessmentRepository
from app.services.corpus_seed import sync_bank, REGISTRY_KEY
from app.services.evidence_context import capture_question
from app.services.practice_config import CELL_QUOTA, MAX_QUESTIONS, QUESTION_TYPES, difficulty_band
from app.services.practice_corpus import coverage, template_pack, RESULTS_PATH, result_key
from app.validate_bank import load_corpus
from test_ai_admin import _make_account


def test_all_concept_difficulty_type_cells_have_derived_capacity():
    packs, _ = load_corpus()
    codes = {c["concept_code"] for pack in packs for c in pack["concepts"]}
    assert len(codes) == 80
    assert CELL_QUOTA * len(QUESTION_TYPES) >= MAX_QUESTIONS
    counts = coverage([q for pack in packs for q in pack["questions"]], codes)
    assert len(counts) * 3 * len(QUESTION_TYPES) == 720
    assert all(n >= CELL_QUOTA for bands in counts.values() for types in bands.values() for n in types.values())
    assert len(template_pack()["questions"]) == len(codes) * 3 * len(QUESTION_TYPES) * CELL_QUOTA


def test_every_template_answer_is_bound_to_the_actual_fixture_and_query():
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))["results"]
    for q in template_pack()["questions"]:
        if q["question_type"] == "sql":
            for d in q["datasets"]:
                assert results[result_key(d["setup_sql"], q["reference_answer"])] == d["expected_result"]
    with pytest.raises(KeyError):
        results[result_key("CREATE TABLE changed(id int);", "SELECT 1")]


def test_each_case_cell_has_distinct_worked_results_and_grounded_answers():
    from collections import defaultdict
    worked, expected = defaultdict(set), {}
    for q in template_pack()["questions"]:
        if q["question_type"] != "sql":
            continue
        grid = {k: q["datasets"][0]["expected_result"][k] for k in ("columns", "rows")}
        value = json.dumps(grid, ensure_ascii=False, separators=(",", ":"))
        worked[q["concept_codes"][0], difficulty_band(q["difficulty_level"])].add(value)
        expected[q["key"].rsplit("-", 1)[0]] = value
    for q in template_pack()["questions"]:
        value = expected[q["key"].rsplit("-", 1)[0]]
        if q["question_type"] == "mcq":
            assert [o["option_text"] for o in q["options"] if o["is_correct"]] == [value]
        elif q["question_type"] == "essay":
            assert value in q["reference_answer"]
    insufficient = {str(cell): len(values) for cell, values in worked.items() if len(values) < CELL_QUOTA}
    assert len(worked) == 240 and not insufficient, insufficient


@pytest.mark.parametrize("referenced,owner_edit", [(False, False), (True, False), (True, True)])
def test_case_fixture_revision_preserves_native_history_and_owner_decisions(db_session, referenced, owner_edit):
    key = "case-sql-select-easy-1-sql"
    old = json.loads((ROOT_DIR / "db/reviewed_question_before.json").read_text(encoding="utf-8"))[key]["question"]
    packs, _ = load_corpus()
    concept = next(c for p in packs for c in p["concepts"] if c["concept_code"] == "SQL-SELECT")
    pack = {"concepts": [concept], "clos": [], "dependencies": {}, "assessments": [], "questions": [old]}
    admin = _make_account(db_session, "case-upgrade@test.dev", "Administrator")
    sync_bank(db_session, admin, packs=[pack]); db_session.commit()
    old_id = db_session.get(SystemSetting, REGISTRY_KEY).value["questions"][key]["id"]
    question = db_session.get(Question, old_id)
    if referenced:
        now = datetime.now(timezone.utc)
        session = AssessmentSession(learner_id=admin.account_id, expires_at=now, status="completed")
        db_session.add(session); db_session.flush()
        snapshot = capture_question(AssessmentRepository(db_session), question)
        attempt = Attempt(session_id=session.session_id, question_id=old_id, seq_no=1,
            question_snapshot=snapshot, score=Decimal("0.50"), submitted_at=now, grading_status="graded")
        db_session.add(attempt); db_session.commit()
    if owner_edit:
        question.explanation += " Local owner decision."
        question.status = "draft"
        db_session.commit()
    prior_explanation = question.explanation
    revised = {**pack, "questions": [next(q for q in template_pack()["questions"] if q["key"] == key)]}
    sync_bank(db_session, admin, packs=[revised]); db_session.commit()
    current_id = db_session.get(SystemSetting, REGISTRY_KEY).value["questions"][key]["id"]
    assert (current_id != old_id) == referenced
    if referenced:
        db_session.refresh(attempt)
        assert (attempt.question_id, attempt.question_snapshot, attempt.score) == (old_id, snapshot, Decimal("0.50"))
        assert question.explanation == prior_explanation
    else:
        assert question.tags == ["reviewed-case-v2", "SQL-SELECT", "EASY"]
    if owner_edit:
        assert question.status == "draft"
    assert sync_bank(db_session, admin, packs=[revised]) == {"added": 0, "reviewed": 0, "preserved_edits": 0}


def focused_pack(key):
    packs, translations = load_corpus(include_templates=False)
    pack = deepcopy(next(p for p in packs if any(q["key"] == key for q in p["questions"])))
    pack["questions"] = [q for q in pack["questions"] if q["key"] == key]
    return pack, translations


@pytest.mark.parametrize("referenced", [False, True])
def test_seed_review_updates_unused_id_but_versions_referenced_history(db_session, sandbox_runner, referenced):
    key = "mcq-sql-where"
    pack, translations = focused_pack(key)
    before = json.loads((ROOT_DIR / "db/reviewed_question_before.json").read_text(encoding="utf-8"))[key]
    old = deepcopy(pack)
    old["questions"] = [before["question"]]
    admin = _make_account(db_session, "seed-review@test.dev", "Administrator")
    imported = import_pack(db_session, admin, sandbox_runner, old,
        translation_data={"locale": "vi", "questions": {key: before["translation"]}})
    question = db_session.get(Question, imported["question_ids"][0])
    qid = question.question_id
    if referenced:
        session = AssessmentSession(learner_id=admin.account_id, expires_at=datetime.now(timezone.utc), status="completed")
        db_session.add(session); db_session.flush()
        snapshot = capture_question(AssessmentRepository(db_session), question)
        attempt = Attempt(session_id=session.session_id, question_id=qid, seq_no=1, question_snapshot=snapshot, score=1)
        db_session.add(attempt); db_session.commit()
    result = sync_bank(db_session, admin, packs=[pack], translations=translations)
    db_session.commit()
    assert result == {"added": 0, "reviewed": 1, "preserved_edits": 0}
    registry = db_session.get(SystemSetting, REGISTRY_KEY).value["questions"][key]
    current = db_session.get(Question, registry["id"])
    assert current.explanation == pack["questions"][0]["explanation"]
    if referenced:
        db_session.refresh(attempt)
        assert current.question_id != qid and current.family_id == qid and current.version_no == 2
        assert attempt.question_id == qid and attempt.question_snapshot == snapshot and attempt.score == 1
        assert question.status == "retired"
    else:
        assert current.question_id == qid
    assert sync_bank(db_session, admin, packs=[pack], translations=translations) == {"added": 0, "reviewed": 0, "preserved_edits": 0}


def test_seed_preserves_unreviewed_owner_edit_and_adds_reviewed_copy(db_session, sandbox_runner):
    pack, translations = focused_pack("mcq-sql-select")
    admin = _make_account(db_session, "seed-owner@test.dev", "Administrator")
    result = import_pack(db_session, admin, sandbox_runner, pack)
    owner = db_session.get(Question, result["question_ids"][0])
    owner.explanation += " Owner's reviewed local annotation."
    owner.status = "draft"
    db_session.commit()
    original = owner.explanation
    changed = sync_bank(db_session, admin, packs=[pack], translations=translations)
    db_session.commit()
    assert changed["added"] == changed["preserved_edits"] == 1
    assert owner.explanation == original and owner.status == "draft"
    assert db_session.scalar(select(func.count()).select_from(Question)) == 2
    assert sync_bank(db_session, admin, packs=[pack], translations=translations)["added"] == 0


def test_source_failure_cannot_write_any_curriculum_or_questions(db_session):
    pack, translations = focused_pack("mcq-sql-select")
    pack["questions"][0]["options"][1]["is_correct"] = True
    admin = _make_account(db_session, "seed-invalid@test.dev", "Administrator")
    with pytest.raises(ValueError, match="failed validation"):
        sync_bank(db_session, admin, packs=[pack], translations=translations)
    assert db_session.scalar(select(func.count()).select_from(Question)) == 0


def test_normalization_sample_dependencies_keys_and_lossless_decomposition(db_session):
    """The PG manual describes FDs/constraints; verify this theory separately."""
    from itertools import combinations
    from sqlalchemy import text
    attributes = {"student_id", "student_name", "course_id", "course_title", "dept_id", "dept_name", "grade"}
    dependencies = [({"student_id"}, {"student_name", "dept_id"}), ({"course_id"}, {"course_title"}),
                    ({"dept_id"}, {"dept_name"}), ({"student_id", "course_id"}, {"grade"})]
    def closure(keys):
        found = set(keys)
        while True:
            expanded = found | set().union(*(right for left, right in dependencies if left <= found))
            if expanded == found:
                return found
            found = expanded
    candidates = [set(keys) for n in range(1, len(attributes)+1) for keys in combinations(sorted(attributes), n)
                  if closure(keys) == attributes and all(closure(set(keys)-{key}) != attributes for key in keys)]
    assert candidates == [{"student_id", "course_id"}]
    relations = [{"student_id", "student_name", "dept_id"}, {"dept_id", "dept_name"},
                 {"course_id", "course_title"}, {"student_id", "course_id", "grade"}]
    assert all(any(left | right <= relation for relation in relations) for left, right in dependencies)
    rows = db_session.execute(text("""WITH original(sid,sname,cid,ctitle,did,dname,grade) AS
        (VALUES(1,'An',10,'SQL',2,'CS',8),(1,'An',11,'Design',2,'CS',7),(2,'Binh',10,'SQL',3,'Math',9)),
        student AS(SELECT DISTINCT sid,sname,did FROM original), department AS(SELECT DISTINCT did,dname FROM original),
        course AS(SELECT DISTINCT cid,ctitle FROM original), enrollment AS(SELECT sid,cid,grade FROM original),
        restored AS(SELECT sid,sname,cid,ctitle,did,dname,grade FROM enrollment JOIN student USING(sid)
            JOIN department USING(did) JOIN course USING(cid))
        SELECT * FROM ((SELECT * FROM original EXCEPT ALL SELECT * FROM restored)
            UNION ALL (SELECT * FROM restored EXCEPT ALL SELECT * FROM original)) difference""")).all()
    assert rows == []


@pytest.mark.parametrize("referenced,owner_edit", [(False, False), (True, False), (True, True)])
def test_registered_source_revision_preserves_history_and_local_edits(db_session, referenced, owner_edit):
    pack, translations = focused_pack("mcq-sql-select")
    admin = _make_account(db_session, "seed-revision@test.dev", "Administrator")
    first = sync_bank(db_session, admin, packs=[pack], translations=translations)
    assert first["added"] == 1
    db_session.commit()
    question = db_session.scalar(select(Question))
    old_id = question.question_id
    if referenced:
        session = AssessmentSession(learner_id=admin.account_id, expires_at=datetime.now(timezone.utc), status="completed")
        db_session.add(session); db_session.flush()
        snapshot = capture_question(AssessmentRepository(db_session), question)
        attempt = Attempt(session_id=session.session_id, question_id=old_id, seq_no=1, question_snapshot=snapshot, score=.5)
        db_session.add(attempt)
    if owner_edit:
        question.explanation += " Local owner decision."
    old_explanation = question.explanation
    db_session.commit()
    revised = deepcopy(pack)
    revised["questions"][0]["explanation"] += " Projection also retains NULL values."
    result = sync_bank(db_session, admin, packs=[revised], translations=translations)
    db_session.commit()
    current_id = db_session.get(SystemSetting, REGISTRY_KEY).value["questions"]["mcq-sql-select"]["id"]
    if owner_edit:
        assert result["preserved_edits"] == result["added"] == 1 and question.explanation == old_explanation
    else:
        assert result["reviewed"] == 1 and result["added"] == 0
    assert (current_id != old_id) == referenced
    if referenced:
        db_session.refresh(attempt)
        assert attempt.question_id == old_id and attempt.question_snapshot == snapshot and attempt.score == Decimal("0.50")
