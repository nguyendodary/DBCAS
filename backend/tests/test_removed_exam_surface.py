"""Current public API rejects every retired exam-management operation."""
import json
from pathlib import Path
import pytest
from sqlalchemy import func, select
from app.main import app
from app.models import Assessment
from test_adaptive_engine import _make_account
from test_supervisor_requirements import headers


@pytest.mark.parametrize("method,path", [
    ("get", "/admin/assessments"), ("post", "/admin/assessments"),
    ("get", "/admin/assessments/1"), ("put", "/admin/assessments/1"),
    ("patch", "/admin/assessments/1"), ("delete", "/admin/assessments/1"),
    ("get", "/admin/assessments/1/questions"), ("put", "/admin/assessments/1/questions"),
])
def test_exam_management_is_absent_for_admin_and_learner(client, db_session, method, path):
    admin = _make_account(db_session, "retired-admin@test.dev", "Administrator")
    learner = _make_account(db_session, "retired-learner@test.dev", "Learner")
    for account in (admin, learner, None):
        response = getattr(client, method)("/api/v1" + path, headers=headers(account) if account else {})
        assert response.status_code == 404
    assert not any('/admin/assessments' in path for path in app.openapi()["paths"])
    assert db_session.scalar(select(func.count()).select_from(Assessment)) == 0


def test_runtime_bank_packs_have_no_prebuilt_exams():
    root = Path(__file__).resolve().parents[2]
    for name in ("benchmark_pack.json", "sql_knowledge_pack.json", "postgres_knowledge_pack.json"):
        assert json.loads((root / "db" / name).read_text(encoding="utf-8"))["assessments"] == []
