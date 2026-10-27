"""Authoring APIs must present grading bands consistently, with criteria intact."""
from copy import deepcopy
from decimal import Decimal
import pytest
from sqlalchemy import text

from app.db import get_db, get_session_factory
from app.main import app

from test_adaptive_engine import _make_account
from test_llm_release import RUBRICS
from test_supervisor_requirements import headers


@pytest.mark.parametrize("ordering", [(0, 1, 2, 3), (2, 0, 3, 1)])
def test_essay_authoring_preserves_input_order_after_storage_reorganization(client, db_session, ordering):
    admin = _make_account(db_session, "rubric-order@test.dev", "Administrator")
    bands = deepcopy(RUBRICS)
    for band in bands:
        band["criteria"] = f"Tiêu chí gốc {band['level_name']}"
    response = client.post("/api/v1/admin/questions", headers=headers(admin, "Administrator"), json={
        "question_type": "essay", "prompt": "Giải thích chuẩn hóa.", "original_locale": "vi",
        "difficulty_level": 3, "points": 1, "reference_answer": "Giảm dư thừa theo các phụ thuộc hàm.",
        "rubrics": [bands[i] for i in ordering],
    })
    assert response.status_code == 201, response.json()
    qid = response.json()["question_id"]
    expected = [bands[i] for i in ordering]
    # A legitimate storage reorganization must not change authoring intent.
    # This runs only on the disposable PostgreSQL fixture, with no data edits.
    db_session.execute(text("CREATE INDEX rubric_storage_order_test ON rubric(min_score DESC, rubric_id DESC)"))
    db_session.execute(text("CLUSTER rubric USING rubric_storage_order_test"))
    db_session.commit()
    def heap_scan_db():
        with get_session_factory()() as db:
            db.execute(text("SET LOCAL enable_indexscan=off"))
            db.execute(text("SET LOCAL enable_bitmapscan=off"))
            yield db
    original = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = heap_scan_db
    try:
        retrieved = client.get(f"/api/v1/admin/questions/{qid}", headers=headers(admin, "Administrator"))
        assert retrieved.status_code == 200
        for detail in (response.json(), retrieved.json()):
            assert [r["level_name"] for r in detail["rubrics"]] == [r["level_name"] for r in expected]
            assert [r["criteria"] for r in detail["rubrics"]] == [r["criteria"] for r in expected]
            assert [(Decimal(r["min_score"]), Decimal(r["max_score"])) for r in detail["rubrics"]] == [
                (Decimal(str(r["min_score"])), Decimal(str(r["max_score"]))) for r in expected]
    finally:
        if original is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = original
        db_session.execute(text("DROP INDEX rubric_storage_order_test"))
        db_session.commit()
