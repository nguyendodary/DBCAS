"""Fixed question sets and deferred grading, without touching any database."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest

from app.errors import AppError
from app.services import adaptive_engine as engine, assessment_lifecycle as lifecycle
from app.services.personalized_assessment import select_questions


def test_fixed_plan_keeps_format_quotas_and_unique_version_families():
    pool = [(NS(question_id=i, family_id=i, question_type=kind), [i % 4 + 1])
            for kind, ids in (("mcq", range(1, 16)), ("sql", range(16, 20)), ("essay", range(20, 23)))
            for i in ids]
    pool.append((NS(question_id=100, family_id=1, question_type="mcq"), [1]))
    chosen = select_questions(pool, [], {"mcq": 10, "sql": 2, "essay": 1})
    assert len(chosen) == len({q.family_id for q in chosen}) == 13
    assert [sum(q.question_type == kind for q in chosen) for kind in ("mcq", "sql", "essay")] == [10, 2, 1]


def test_state_exposes_all_fixed_questions_and_counts_drafts_not_grades(monkeypatch):
    now = datetime.now(timezone.utc)
    attempts = [NS(submitted_at=None, draft_answer=answer, seq_no=i + 1)
                for i, answer in enumerate([{"selected_option_ids": [5, 6]}, {"sql_answer": "  "}, {"essay_answer": "An answer"}])]
    session = NS(session_id=1, assessment_id=2, config_snapshot={"navigation_mode": "FREE"},
                 started_at=now, expires_at=now + timedelta(hours=1), submitted_at=None,
                 status="in_progress", locale="vi", result_release_policy="IMMEDIATE", release_status="unsubmitted")
    repo = Mock()
    repo.session_attempts.return_value = attempts
    repo.server_time.return_value = now
    monkeypatch.setattr(engine, "assessment_view", lambda *args: NS(title="Fixed exam", max_questions=3))
    monkeypatch.setattr(engine, "_served_question", lambda repo, a, locale: dict(
        attempt_id=a.seq_no, seq_no=a.seq_no, question_id=a.seq_no, question_type="essay",
        prompt="Question", difficulty_level=1, points="1", concepts=[], options=[], draft=a.draft_answer))
    state = engine._state(repo, session)
    assert state.navigation_mode == "FREE"
    assert len(state.questions) == state.served_count == 3
    assert state.answered_count == 2
    assert state.current_question.seq_no == 2
    assert not state.done
    assert all(q.score is None and q.submitted_at is None for q in state.questions)


def test_free_session_cannot_grade_individual_answers(monkeypatch):
    monkeypatch.setattr(lifecycle, "owned_locked_session", lambda *args: NS(config_snapshot={"navigation_mode": "FREE"}))
    grader = Mock()
    monkeypatch.setattr(lifecycle, "grade_attempt", grader)
    with pytest.raises(AppError) as error:
        lifecycle.submit(Mock(), 1, NS(account_id=2), NS(question_id=3))
    assert error.value.code == "finish_required"
    grader.assert_not_called()


def test_legacy_navigation_materializes_remainder_and_preserves_existing_evidence(monkeypatch):
    repo, db = Mock(), Mock()
    assessment = NS(max_questions=3, target_mcq=2, target_sql=1, target_essay=0)
    session = NS(session_id=8, config_snapshot={"version": 1})
    submitted = NS(question_id=1, seq_no=1, submitted_at="original", draft_answer={"selected_option_id": 10}, score="1")
    attempts = [submitted]
    sql = NS(question_id=3, family_id=3, question_type="sql", difficulty_level=2)
    mcq = NS(question_id=2, family_id=2, question_type="mcq", difficulty_level=1)
    repo.session_attempts.side_effect = lambda _: list(attempts)
    monkeypatch.setattr(engine, "AssessmentRepository", lambda _: repo)
    monkeypatch.setattr(engine, "load_owned_active_session", lambda *args: session)
    monkeypatch.setattr(engine, "free_navigation", lambda *args: False)
    monkeypatch.setattr(engine, "assessment_view", lambda *args: assessment)
    monkeypatch.setattr(engine, "question_view", lambda _: NS(question_type="mcq"))
    monkeypatch.setattr(engine, "_eligible_pool", lambda *args: [(mcq, [1]), (sql, [1])])
    monkeypatch.setattr(engine, "_state", lambda *args: "fixed state")
    def serve(repo, session, question, seq, detail):
        attempts.append(NS(question_id=question.question_id, seq_no=seq))
    monkeypatch.setattr(engine, "_serve", serve)
    assert engine.enable_navigation(db, 8, NS(account_id=1)) == "fixed state"
    assert [a.question_id for a in attempts] == [1, 2, 3]
    assert submitted.submitted_at == "original" and submitted.score == "1"
    assert submitted.draft_answer == {"selected_option_id": 10}
    assert session.config_snapshot == {"version": 1}
    assert len(db.add_all.call_args.args[0]) == 3
    db.commit.assert_called_once()
