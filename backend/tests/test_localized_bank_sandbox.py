"""Execute every checked-in SQL reference against disposable sandbox fixtures."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.config import get_settings
from app.services.bank_validation import sql_fixture_problems, verify_sql_fixtures
from app.services.sandbox_runner import SandboxRunner


ROOT = Path(__file__).resolve().parents[2]
PACKS = [json.loads((ROOT / "db" / name).read_text(encoding="utf-8"))
         for name in ("benchmark_pack.json", "sql_knowledge_pack.json", "postgres_knowledge_pack.json")]
SQL_QUESTIONS = [question for pack in PACKS for question in pack["questions"]
                 if question["question_type"] == "sql"]


@pytest.mark.parametrize("question", SQL_QUESTIONS, ids=lambda question: question["key"])
def test_localized_sql_reference_keeps_expected_results(question):
    datasets = [SimpleNamespace(**row) for row in question["datasets"]]
    assert sql_fixture_problems(datasets, question["reference_answer"]) == []
    assert verify_sql_fixtures(SandboxRunner(get_settings()), datasets, question["reference_answer"]) == []


def test_fresh_bank_import_is_bilingual_and_idempotent(db_session):
    from sqlalchemy import func, select
    from app.benchmark import import_pack
    from app.models import Question, QuestionTranslation
    from app.services.question_localization import translation_is_current
    from test_ai_admin import _make_account

    admin = _make_account(db_session, "bilingual-import@test.dev", "Administrator")
    runner = SandboxRunner(get_settings())
    first = [import_pack(db_session, admin, runner, pack) for pack in PACKS]
    second = [import_pack(db_session, admin, runner, pack) for pack in PACKS]
    assert first == second
    assert db_session.scalar(select(func.count()).select_from(Question)) == 442
    assert db_session.scalar(select(func.count()).select_from(QuestionTranslation)) == 442
    assert db_session.scalar(select(func.count()).select_from(Question).where(Question.status == "validated")) == 441
    assert db_session.scalar(select(func.count()).select_from(Question).where(Question.status == "retired")) == 1
    counts = dict(db_session.execute(select(Question.question_type, func.count()).group_by(Question.question_type)).all())
    assert counts == {"mcq": 326, "sql": 67, "essay": 49}
    assert all(translation_is_current(question, row)
               for question in db_session.scalars(select(Question)) for row in question.translations)
    from app.services.question_service import get_question
    question = db_session.scalar(select(Question).order_by(Question.question_id))
    assert get_question(db_session, question.question_id).translations[0].current
    question.prompt += " Edited canonical content."
    db_session.flush()
    detail = get_question(db_session, question.question_id)
    assert not detail.translations[0].current
    assert "vi" in detail.missing_locales and "vi" not in detail.translation_locales


def test_all_essay_rubrics_match_the_canonical_grading_contract():
    from app.services.rubric_validation import rubric_problems
    essays = [question for pack in PACKS for question in pack["questions"]
              if question["question_type"] == "essay" and question.get("status") != "retired"]
    assert len(essays) == 48
    for question in essays:
        assert rubric_problems(question["rubrics"], question["points"]) == [], question["key"]


def test_legacy_essay_is_retired_with_unchanged_history_and_selectable_successor(db_session):
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select, func
    from app.benchmark import import_pack
    from app.models import AssessmentSession, Attempt, Question
    from app.repositories import AssessmentRepository
    from app.services.adaptive_engine import _eligible_pool, get_evidence
    from app.services.evidence_context import capture_question
    from app.services.rubric_validation import rubric_problems
    from test_ai_admin import _make_account

    admin = _make_account(db_session, "legacy-history@test.dev", "Administrator")
    runner = SandboxRunner(get_settings())
    imported = import_pack(db_session, admin, runner, PACKS[0])
    question = db_session.scalar(select(Question).where(Question.prompt ==
        "Explain why indexes speed up reads but slow down writes."))
    successor = db_session.scalar(select(Question).where(Question.prompt.like("A PostgreSQL table is read frequently%")))
    assert question.status == "retired" and successor.status == "validated"
    assert question.question_id != successor.question_id
    assert [(r.level_name, int(r.min_score), int(r.max_score)) for r in question.rubrics] == [
        ("Missing", 0, 0), ("Partial", 1, 3), ("Complete", 4, 5)]
    assert rubric_problems(successor.rubrics, successor.points) == []
    qid, version = question.question_id, question.version_no
    # Simulate the existing development bank: ID 5 was historically marked
    # validated even though the current grader excludes its three-band rubric.
    question.status = "validated"
    db_session.commit()
    session = AssessmentSession(assessment_id=imported["assessment_ids"][0], learner_id=admin.account_id,
                                status="completed", expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                                locale="en")
    db_session.add(session)
    db_session.flush()
    snapshot = capture_question(AssessmentRepository(db_session), question)
    attempt = Attempt(session_id=session.session_id, question_id=qid, seq_no=1,
                      question_snapshot=snapshot, score=2, submitted_at=datetime.now(timezone.utc),
                      grading_status="graded")
    db_session.add(attempt)
    new_snapshot = capture_question(AssessmentRepository(db_session), successor)
    new_attempt = Attempt(session_id=session.session_id, question_id=successor.question_id, seq_no=2,
                          question_snapshot=new_snapshot, score=4, submitted_at=datetime.now(timezone.utc),
                          grading_status="graded")
    db_session.add(new_attempt)
    db_session.commit()
    first = import_pack(db_session, admin, runner, PACKS[0])
    second = import_pack(db_session, admin, runner, PACKS[0])
    assert first == second == imported
    assert question.question_id == qid and question.version_no == version
    assert question.status == "retired"
    assert db_session.scalar(select(func.count()).select_from(Question)) == 24
    db_session.refresh(attempt)
    assert attempt.question_snapshot == snapshot
    assert len(attempt.question_snapshot["rubrics"]) == 3
    db_session.refresh(new_attempt)
    assert new_attempt.question_snapshot == new_snapshot
    assert len(new_attempt.question_snapshot["rubrics"]) == 4
    evidence = get_evidence(db_session, session.session_id, admin)
    assert evidence.items[0].question_id == qid
    assert evidence.items[0].prompt == question.prompt
    assert evidence.items[0].score == 2
    assert [band.level_name for band in evidence.items[0].rubrics] == ["Missing", "Partial", "Complete"]
    assert evidence.items[1].question_id == successor.question_id
    assert len(evidence.items[1].rubrics) == 4
    from types import SimpleNamespace
    idx = next(tag.concept_id for tag in question.concept_tags if tag.confirmed)
    target = SimpleNamespace(concept_id=idx, min_difficulty=1, max_difficulty=5)
    selected = _eligible_pool(SimpleNamespace(targets=[target]), set(), AssessmentRepository(db_session))
    assert successor.question_id in [item.question_id for item, _ in selected]
    assert qid not in [item.question_id for item, _ in selected]
