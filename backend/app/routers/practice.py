"""Minimal practice, evaluation and local administration endpoints."""
from typing import Literal
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session
from ..db import get_db
from ..deps import LearnerOnly, AdminOnly, get_sandbox_runner, get_llm_service
from ..models import Account
from ..schemas import RunSqlRequest, SqlRunResult, SessionStateResult
from ..services import practice_service, evaluation_service, system_settings

router = APIRouter(tags=["practice"])


@router.get("/practice/options")
def practice_options(_: Account = LearnerOnly, db: Session = Depends(get_db)):
    from sqlalchemy import select
    from ..models import Concept
    return {"concepts": [{"concept_id": c.concept_id, "concept_name": c.concept_name, "subject_area": c.subject_area}
                         for c in db.scalars(select(Concept).order_by(Concept.subject_area, Concept.concept_name))],
            "result_flow": system_settings.result_flow(db)}


@router.post("/practice/start", response_model=SessionStateResult)
def start_practice(payload: practice_service.PracticeStart, request: Request, learner: Account = LearnerOnly,
                   db: Session = Depends(get_db), runner=Depends(get_sandbox_runner), llm=Depends(get_llm_service)):
    from ..services.question_localization import normalize_locale
    from ..services.llm import LLMService
    if isinstance(llm, LLMService):
        llm = llm.with_budget(timeout_seconds=10, max_retries=1)
    return practice_service.start(db, learner, payload, runner, llm, locale=normalize_locale(request.headers.get("accept-language", "vi")))


@router.get("/evaluations/overall")
def overall_evaluation(learner: Account = LearnerOnly, db: Session = Depends(get_db)):
    return evaluation_service.view(db, learner.account_id)


@router.post("/evaluations/overall/retry")
def retry_overall(learner: Account = LearnerOnly, db: Session = Depends(get_db)):
    return evaluation_service.view(db, learner.account_id, retry=True)


@router.get("/evaluations/attempts/{session_id}")
def attempt_evaluation(session_id: int, learner: Account = LearnerOnly, db: Session = Depends(get_db)):
    return evaluation_service.view(db, learner.account_id, session_id)


@router.post("/evaluations/attempts/{session_id}/retry")
def retry_attempt(session_id: int, learner: Account = LearnerOnly, db: Session = Depends(get_db)):
    return evaluation_service.view(db, learner.account_id, session_id, retry=True)


class FlowUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    result_flow: Literal["IMMEDIATE", "HUMAN_VERIFIED"]


@router.get("/admin/system")
def system_status(_: Account = AdminOnly, db: Session = Depends(get_db)):
    return system_settings.status(db)


@router.put("/admin/system")
def update_system(payload: FlowUpdate, admin: Account = AdminOnly, db: Session = Depends(get_db)):
    return system_settings.update_flow(db, payload.result_flow, admin)


class AdminPasswordReset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str

    @field_validator("password")
    @classmethod
    def password_policy(cls, value):
        from ..schemas import _validate_password
        return _validate_password(value)


@router.post("/admin/accounts/{account_id}/reset-password")
def reset_account_password(account_id: int, payload: AdminPasswordReset, admin: Account = AdminOnly,
                           db: Session = Depends(get_db)):
    from datetime import datetime, timezone
    from sqlalchemy import update
    from ..models import RefreshSession, PasswordResetToken, PasswordResetAudit
    from ..repositories import AccountRepository
    from ..security import hash_password
    from ..errors import AppError
    target = AccountRepository(db).get_for_update(account_id)
    if not target: raise AppError(404, "account_not_found", "Không tìm thấy tài khoản.")
    if account_id == admin.account_id or (any(r.role_name == "Administrator" for r in target.roles) and not admin.can_manage_roles):
        raise AppError(403, "forbidden", "Không thể đặt lại mật khẩu cho tài khoản này.")
    now = datetime.now(timezone.utc)
    target.password_hash, target.password_set, target.password_changed_at = hash_password(payload.password), True, now
    db.execute(update(RefreshSession).where(RefreshSession.account_id == account_id, RefreshSession.revoked_at.is_(None)).values(revoked_at=now))
    db.execute(update(PasswordResetToken).where(PasswordResetToken.account_id == account_id, PasswordResetToken.revoked_at.is_(None)).values(revoked_at=now))
    db.add(PasswordResetAudit(account_id=account_id, event="completed"))
    db.commit()
    return {"status": "ok"}


@router.post("/admin/grading-reviews/{session_id}/run-sql", response_model=SqlRunResult)
def verify_sql(session_id: int, payload: RunSqlRequest, _: Account = AdminOnly,
               db: Session = Depends(get_db), runner=Depends(get_sandbox_runner)):
    from ..repositories import AssessmentRepository
    from ..services.evidence_context import question_view
    from ..errors import AppError
    from ..services.sandbox_runner import SandboxError
    session = AssessmentRepository(db).get_session(session_id)
    attempt = AssessmentRepository(db).get_attempt(session_id, payload.question_id)
    if not session or not attempt: raise AppError(404, "attempt_not_found", "Không tìm thấy bài làm.")
    question = question_view(attempt)
    if question.question_type != "sql": raise AppError(422, "unsupported_question_type", "Chỉ chạy câu SQL.")
    primary = next((d for d in question.datasets if not d.is_edge_case), None)
    if not primary: raise AppError(422, "dataset_not_configured", "Câu hỏi chưa có dữ liệu SQL.")
    try:
        schema = runner.provision_dataset(primary.setup_sql)
        try: result = runner.execute(payload.sql, schema=schema)
        finally: runner.drop_dataset(schema)
    except SandboxError as exc:
        raise AppError(503, exc.code, "Sandbox tạm thời chưa sẵn sàng. Hãy thử lại.") from None
    return SqlRunResult(**{key: getattr(result, key) for key in SqlRunResult.model_fields})
