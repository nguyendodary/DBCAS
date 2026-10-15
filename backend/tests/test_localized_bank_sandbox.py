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
    assert db_session.scalar(select(func.count()).select_from(Question)) == 441
    assert db_session.scalar(select(func.count()).select_from(QuestionTranslation)) == 441
    counts = dict(db_session.execute(select(Question.question_type, func.count()).group_by(Question.question_type)).all())
    assert counts == {"mcq": 326, "sql": 67, "essay": 48}
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
    essays = [question for pack in PACKS for question in pack["questions"] if question["question_type"] == "essay"]
    assert len(essays) == 48
    for question in essays:
        assert rubric_problems(question["rubrics"], question["points"]) == [], question["key"]


@pytest.mark.parametrize("snapshotted", [True, False])
def test_legacy_rubric_repair_is_explicit_idempotent_and_preserves_evidence(db_session, snapshotted):
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select, func
    from app.benchmark import import_pack
    from app.errors import AppError
    from app.models import AssessmentSession, Attempt, Question
    from app.repositories import QuestionRepository, AssessmentRepository
    from app.schemas import RubricInput
    from app.services.evidence_context import capture_question
    from app.services.legacy_rubric_repair import HISTORICAL_INDEX_RUBRIC
    from test_ai_admin import _make_account

    admin = _make_account(db_session, "legacy-repair@test.dev", "Administrator")
    runner = SandboxRunner(get_settings())
    imported = import_pack(db_session, admin, runner, PACKS[0])
    question = db_session.scalar(select(Question).where(Question.prompt ==
        "Explain why indexes speed up reads but slow down writes."))
    qid, version = question.question_id, question.version_no
    repo = QuestionRepository(db_session)
    repo.replace_rubrics(question, [RubricInput(**row) for row in HISTORICAL_INDEX_RUBRIC])
    db_session.flush()
    db_session.expire(question, ["rubrics"])
    session = AssessmentSession(assessment_id=imported["assessment_ids"][0], learner_id=admin.account_id,
                                expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    db_session.add(session)
    db_session.flush()
    snapshot = capture_question(AssessmentRepository(db_session), question) if snapshotted else None
    attempt = Attempt(session_id=session.session_id, question_id=qid, seq_no=1, question_snapshot=snapshot)
    db_session.add(attempt)
    db_session.commit()
    with pytest.raises(AppError) as rejected:
        import_pack(db_session, admin, runner, PACKS[0])
    assert rejected.value.code == "benchmark_question_conflict"
    if not snapshotted:
        with pytest.raises(AppError) as rejected:
            import_pack(db_session, admin, runner, PACKS[0], repair_legacy_index_rubric=True)
        assert rejected.value.code == "legacy_evidence_requires_snapshot"
        assert len(question.rubrics) == 3
        return
    first = import_pack(db_session, admin, runner, PACKS[0], repair_legacy_index_rubric=True)
    second = import_pack(db_session, admin, runner, PACKS[0], repair_legacy_index_rubric=True)
    assert first == second == imported
    assert question.question_id == qid and question.version_no == version + 1
    assert db_session.scalar(select(func.count()).select_from(Question)) == 23
    db_session.refresh(attempt)
    assert attempt.question_snapshot == snapshot
    assert len(attempt.question_snapshot["rubrics"]) == 3
    assert len(question.rubrics) == 4
