"""Real database, bank validation and grading for repeatable local initialization."""
import pytest
from sqlalchemy import func, select

from app.models import Account, Assessment, AssessmentSession, Attempt, Question
from app.repositories import AccountRepository
from app.seed_demo import DEMO_ADMIN, DEMO_LEARNER, DEMO_PASSWORD, seed_demo
from app.security import verify_password
from app.services.statistics_service import dashboard


def test_demo_seed_creates_real_published_evidence_and_preserves_edits(db_session, sandbox_runner):
    result = seed_demo(db_session, sandbox_runner, deployment_mode="development")
    assert result["history_count"] == 4
    admin = AccountRepository(db_session).find_by_email(DEMO_ADMIN)
    learner = AccountRepository(db_session).find_by_email(DEMO_LEARNER)
    assert admin.can_manage_roles and admin.status == "active"
    assert verify_password(DEMO_PASSWORD, admin.password_hash)
    assert verify_password(DEMO_PASSWORD, learner.password_hash)
    assert db_session.scalar(select(func.count()).select_from(Account)) == 4
    assert db_session.scalar(select(func.count()).select_from(Question)) == 24
    assert result["exam_count"] == 0
    assert db_session.scalar(select(func.count()).select_from(Assessment)) == 0
    sessions = list(db_session.scalars(select(AssessmentSession)))
    assert len(sessions) == 4 and all(s.release_status == "published" for s in sessions)
    assert all(s.assessment_id is None and s.result_release_policy == "HUMAN_VERIFIED" for s in sessions)
    for session in sessions:
        attempts = list(db_session.scalars(select(Attempt).where(Attempt.session_id == session.session_id)))
        assert len(attempts) == 13 and all(a.score is not None and a.question_snapshot for a in attempts)
        assert {a.question_snapshot["question_type"] for a in attempts} == {"mcq", "sql", "essay"}
    stats = dashboard(db_session, learner_id=learner.account_id)
    assert stats["published_formal_sessions"] == 2
    assert stats["dimensions"]["clos"] and stats["recommendations"]
    learner.profile.full_name = "Updated by the learner"
    old_hash = learner.password_hash
    db_session.commit()
    assert seed_demo(db_session, sandbox_runner, deployment_mode="development") == {"created": False}
    assert learner.profile.full_name == "Updated by the learner" and learner.password_hash == old_hash
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 4


@pytest.mark.parametrize("mode", ["production", "staging"])
def test_demo_seed_refuses_nonlocal_modes_before_writing(db_session, sandbox_runner, mode):
    with pytest.raises(ValueError, match="forbidden"):
        seed_demo(db_session, sandbox_runner, deployment_mode=mode)
    assert db_session.scalar(select(func.count()).select_from(Account)) == 0


def test_failed_initialization_rolls_back_accounts_so_restart_can_retry(db_session, sandbox_runner, monkeypatch):
    from app import seed_demo as module
    from app.config import get_settings

    def fail_import(*args, **kwargs):
        raise RuntimeError("Fixture validation failed")

    monkeypatch.setattr(module, "import_pack", fail_import)
    with pytest.raises(RuntimeError, match="Fixture validation"):
        module.initialize_demo(get_settings(), sandbox_runner)
    assert db_session.scalar(select(func.count()).select_from(Account)) == 0
