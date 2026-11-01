"""Create local demo data atomically, once; never reset an existing installation."""
import json
from decimal import Decimal

import psycopg
from sqlalchemy import text
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


def _history(db, assessment_id, learner, admin, runner, *, success_every):
    state = adaptive_engine.start_session(db, assessment_id, learner, locale="vi")
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
    grading_review.publish(db, state.session_id, PublishResultsRequest(revision=detail["revision"]), admin)


def seed_demo(db, runner, *, deployment_mode):
    if deployment_mode != "development":
        raise ValueError("Local demo seed is forbidden outside development")
    db.execute(text("SELECT pg_advisory_xact_lock(20261102)"))
    accounts = AccountRepository(db)
    if accounts.find_by_email(DEMO_ADMIN):
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
    pack["assessments"][0].update(title=DEMO_TITLE,
        description="60 phút · 10 trắc nghiệm, 2 SQL, 1 tự luận. Lưu nháp tự động; giảng viên duyệt trước khi công bố.",
        result_release_policy="HUMAN_VERIFIED")
    imported = import_pack(db, admin, runner, pack)
    assessment_id = imported["assessment_ids"][0]
    for learner, every in ((learners[0], 3), (learners[0], 2), (learners[1], 1), (learners[2], 4)):
        _history(db, assessment_id, learner, admin, runner, success_every=every)
    return {"created": True, "assessment_id": assessment_id, "history_count": 4}


def initialize_demo(settings, runner):
    if settings.deployment_mode != "development":
        raise ValueError("Local demo seed is forbidden outside development")
    url = settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(url) as conn:
        initialize(conn, deployment_mode=settings.deployment_mode)
    # Services commit their own work. Savepoints keep all demo creation inside
    # one outer transaction, so a failed seed can safely be retried from scratch.
    with get_engine().begin() as connection:
        with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as db:
            result = seed_demo(db, runner, deployment_mode=settings.deployment_mode)
    return result


def main():
    settings = get_settings()
    result = initialize_demo(settings, build_sandbox_runner(settings))
    print("Local demo data ready" if result["created"] else "Existing local data preserved")


if __name__ == "__main__":
    main()
