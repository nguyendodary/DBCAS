"""Create local demo data atomically, once; never reset an existing installation."""
import json
import logging
import os
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg
from sqlalchemy import func, text, update
from sqlalchemy.orm import Session

from .benchmark import import_pack
from .config import ROOT_DIR, get_settings
from .db import get_engine
from .init_db import initialize
from .models import AccountRoleAudit
from .repositories import AccountRepository, AssessmentRepository
from .schemas import GradeReviewRequest, PublishResultsRequest, SubmitAnswerRequest
from .security import hash_password
from .services import adaptive_engine, grading_review, grading_service
from .services.evidence_context import question_view
from .services.sandbox_runner import build_sandbox_runner

# Public local demonstration credentials, not deployment secrets.
DEMO_PASSWORD = "Demo12345!"
DEMO_ADMIN = "admin@dbcas.local"
DEMO_LEARNER = "learner@dbcas.local"
DEMO_TITLE = "Đánh giá năng lực PostgreSQL"
logger = logging.getLogger("dbcas.seed_demo")
SNAPSHOT_HEADER = "-- dbcas-schema-version:"


def _history(db, concept_ids, learner, admin, runner, *, success_every):
    from .services.practice_service import start, PracticeStart
    from .services import evaluation_service
    state = start(db, learner, PracticeStart(concept_ids=concept_ids, question_count=13, request_id=uuid4()), runner)
    repo = AssessmentRepository(db)
    for index in range(13):
        served = adaptive_engine.serve_next(db, state.session_id, learner)
        if served.question is None:
            raise RuntimeError("Demo assessment did not provide its complete question mix")
        attempt = repo.get_attempt(state.session_id, served.question.question_id)
        question = question_view(attempt)
        correct = index % success_every == 0
        if question.question_type == "mcq":
            answer = {"selected_option_id": next(o.option_id for o in question.options if o.is_correct == correct)}
        elif question.question_type == "sql":
            answer = {"sql_answer": question.reference_answer if correct else "SELECT 0 AS answer"}
        else:
            answer = {"essay_answer": "Chuẩn hóa giúp giảm lặp dữ liệu và tránh bất thường khi thêm, sửa hoặc xóa. "
                      "Cần xác định khóa và phụ thuộc hàm, rồi tách quan hệ sao cho nối lại không mất thông tin. "
                      "Ví dụ thông tin khách hàng nên tách khỏi các dòng đơn hàng để địa chỉ chỉ được cập nhật một nơi."}
        grading_service.submit_answer(db, state.session_id, learner,
            SubmitAnswerRequest(question_id=question.question_id, **answer), runner)
    adaptive_engine.finish_session(db, state.session_id, learner)
    evaluation_service.process_one(db, force_fallback=True)
    detail = grading_review.detail(db, state.session_id)
    for item in detail["items"]:
        if item["question_type"] == "mcq":
            continue
        score = item["automated_score"]
        if score is None:
            score = (Decimal(str(item["points"])) * Decimal("0.75")).quantize(Decimal("0.01"))
        detail = grading_review.approve(db, state.session_id, item["attempt_id"],
            GradeReviewRequest(revision=item["revision"], score=score,
                               comments="Bài demo đã được giảng viên kiểm tra theo đáp án và rubric."), admin)
    # The demo seed is a single batch flow; do not leave its deterministic
    # evaluation behind the admin-edit debounce window.
    from .models import EvaluationRecord
    db.execute(update(EvaluationRecord).where(
        EvaluationRecord.session_id == state.session_id).values(available_at=func.now()))
    db.commit()
    evaluation_service.process_one(db, force_fallback=True)
    detail = grading_review.detail(db, state.session_id)
    grading_review.publish(db, state.session_id, PublishResultsRequest(revision=detail["revision"]), admin)


def seed_demo(db, runner, *, deployment_mode):
    if deployment_mode != "development":
        raise ValueError("Local demo seed is forbidden outside development")
    db.execute(text("SELECT pg_advisory_xact_lock(20261102)"))
    accounts = AccountRepository(db)
    if accounts.find_by_email(DEMO_ADMIN):
        from .services.corpus_seed import sync_bank
        sync_bank(db, accounts.find_by_email(DEMO_ADMIN))
        db.commit()
        return {"created": False}
    admin = accounts.create_provisioned(DEMO_ADMIN, hash_password(DEMO_PASSWORD),
                                       "Quản trị demo", "Administrator")
    admin.status = "active"
    admin.can_manage_roles = True
    db.flush()
    db.add(AccountRoleAudit(action_type="ROLE_MANAGER_BOOTSTRAPPED", target_account_id=admin.account_id))
    learners = [accounts.create_learner(email, hash_password(DEMO_PASSWORD), name) for email, name in (
        (DEMO_LEARNER, "Nguyễn An"), ("linh@dbcas.local", "Trần Khánh Linh"),
        ("minh@dbcas.local", "Lê Quang Minh"))]
    db.commit()
    pack = json.loads((ROOT_DIR / "db/benchmark_pack.json").read_text(encoding="utf-8"))
    pack["assessments"] = []
    imported = import_pack(db, admin, runner, pack)
    for learner, every in ((learners[0], 3), (learners[0], 2), (learners[1], 1), (learners[2], 4)):
        _history(db, sorted(imported["concept_ids"].values()), learner, admin, runner, success_every=every)
    from .services.corpus_seed import sync_bank
    bank = sync_bank(db, admin)
    db.commit()
    return {"created": True, "history_count": 4, "exam_count": 0, "bank": bank}


def _restore_snapshot(url: str, path: str, schema_version: str) -> bool:
    """Restore a version-matched data-only demo dump into an empty database.

    The dump is synthetic demo data only. It is rejected when its schema
    version header does not match the freshly migrated database, and every
    failure leaves the database untouched so the caller can use the full seed.
    """
    snapshot = Path(path)
    if not snapshot.is_file():
        return False
    try:
        with snapshot.open(encoding="utf-8") as handle:
            header = handle.readline().strip()
            if header != f"{SNAPSHOT_HEADER} {schema_version}":
                logger.warning("Demo seed snapshot schema mismatch; using full seed")
                return False
            body = "".join(
                line for line in handle
                if not line.startswith(("\\restrict ", "\\unrestrict "))
            )
            sql = header + "\n" + body
        with psycopg.connect(url) as conn:
            with conn.transaction():
                # psycopg's simple protocol accepts the plain pg_dump script.
                conn.execute(sql, prepare=False)
        return True
    except Exception as exc:  # noqa: BLE001 - fallback must stay available
        logger.warning("Demo seed snapshot restore failed (%s); using full seed", type(exc).__name__)
        return False


def _schema_version(conn) -> str:
    row = conn.execute("SELECT COALESCE(MAX(version), '') FROM schema_migration").fetchone()
    return row[0] if row else ""


def initialize_demo(settings, runner):
    if settings.deployment_mode != "development":
        raise ValueError("Local demo seed is forbidden outside development")
    url = settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(url) as conn:
        initialize(conn, deployment_mode=settings.deployment_mode)
        empty = conn.execute("SELECT NOT EXISTS (SELECT 1 FROM account)").fetchone()[0]
        schema_version = _schema_version(conn)
    snapshot_path = os.environ.get("DBCAS_DEMO_SNAPSHOT", "").strip()
    if empty and snapshot_path and _restore_snapshot(url, snapshot_path, schema_version):
        return {"created": False, "snapshot_restored": True}
    # Services commit their own work. Savepoints keep all demo creation inside
    # one outer transaction, so a failed seed can safely be retried from scratch.
    with get_engine().begin() as connection:
        with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as db:
            result = seed_demo(db, runner, deployment_mode=settings.deployment_mode)
    return result


def main():
    settings = get_settings()
    result = initialize_demo(settings, build_sandbox_runner(settings))
    if result.get("snapshot_restored"):
        print("Demo snapshot restored")
    elif result["created"]:
        print("Local demo data ready")
    else:
        print("Existing local data preserved")


if __name__ == "__main__":
    main()
