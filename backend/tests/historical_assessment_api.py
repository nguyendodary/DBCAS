"""Historical exam regression surface, mounted only inside tests.

The application has no exam management router. This adapter keeps the original
migration/immutable-version service contracts covered while public tests assert
that all removed HTTP routes return 404.
"""
import pytest
from typing import Literal, Optional
from fastapi import APIRouter, FastAPI, Depends, Query
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.errors import register_exception_handlers
from app.db import get_db
from app.deps import AdminOnly
from app.models import Account
from app.services import assessment_service
from app.schemas import (AssessmentQuestionPoolRequest, AssessmentQuestionPoolResult,
    AssessmentDetail, AssessmentListItem, AssessmentUpsertRequest, AssessmentStatusUpdate)

router = APIRouter(prefix="/api/v1/admin")
@router.get("/assessments", response_model=list[AssessmentListItem])
def list_assessments(
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, max_length=200),
    status: Optional[Literal["draft", "published", "closed"]] = None,
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    items = assessment_service.list_assessments(db)
    if q:
        items = [item for item in items if q.casefold() in item.title.casefold()]
    if status:
        items = [item for item in items if item.status == status]
    return items[offset:offset + limit if limit is not None else None]


@router.post("/assessments", status_code=201, response_model=AssessmentDetail)
def create_assessment(
    payload: AssessmentUpsertRequest,
    admin: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return assessment_service.create_assessment(db, payload, admin)


@router.get("/assessments/{assessment_id}", response_model=AssessmentDetail)
def get_assessment(
    assessment_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    return assessment_service.get_assessment(db, assessment_id)


@router.put("/assessments/{assessment_id}", response_model=AssessmentDetail)
def replace_assessment(
    assessment_id: int,
    payload: AssessmentUpsertRequest,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Editable only while draft — 409 once activated (close it and draft
    a new version instead)."""
    return assessment_service.replace_assessment(db, assessment_id, payload)


@router.patch("/assessments/{assessment_id}", response_model=AssessmentDetail)
def set_assessment_status(
    assessment_id: int,
    payload: AssessmentStatusUpdate,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """draft -> active -> closed -> draft. Activation requires at least one
    target concept (invalid config A1)."""
    return assessment_service.set_assessment_status(
        db, assessment_id, payload.status
    )


@router.delete("/assessments/{assessment_id}", status_code=204)
def delete_assessment(
    assessment_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """409 while any session references the assessment."""
    return assessment_service.delete_assessment(db, assessment_id)



@router.get("/assessments/{assessment_id}/questions", response_model=AssessmentQuestionPoolResult)
def assessment_question_pool(assessment_id: int, _: Account = AdminOnly, db: Session = Depends(get_db)):
    from app.services.assessment_pool import get_pool
    return get_pool(db, assessment_id)


@router.put("/assessments/{assessment_id}/questions", response_model=AssessmentQuestionPoolResult)
def set_assessment_question_pool(assessment_id: int, payload: AssessmentQuestionPoolRequest,
                                 _: Account = AdminOnly, db: Session = Depends(get_db)):
    from app.services.assessment_pool import set_pool
    return set_pool(db, assessment_id, payload.question_ids)

@pytest.fixture
def historical_client():
    historical = FastAPI()
    historical.router.routes = [*app.router.routes, *router.routes]
    historical.dependency_overrides = app.dependency_overrides
    register_exception_handlers(historical)
    return TestClient(historical)
