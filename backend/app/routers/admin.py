from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import AdminOnly
from ..models import Account
from ..schemas import (
    AccountSummary,
    AdminLearnerItem,
    AdminLearnerSessionsResult,
    CohortOverviewResult,
    CompetencyProfileResult,
    ConceptPrerequisitesResult,
    ProvisionAccountRequest,
    SetPrerequisitesRequest,
)
from ..services import analytics_service, auth_service, concept_graph_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/accounts", status_code=201, response_model=AccountSummary)
def provision_account(
    payload: ProvisionAccountRequest,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """UC04 — Administrator provisions a new account (starts disabled)."""
    return auth_service.provision_account(db, payload)


@router.put(
    "/concepts/{concept_id}/prerequisites",
    response_model=ConceptPrerequisitesResult,
)
def set_concept_prerequisites(
    concept_id: int,
    payload: SetPrerequisitesRequest,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """UC05 — Administrator replaces a concept's direct prerequisite set in
    the skill graph. Self-edges and duplicate ids are rejected (422), unknown
    concepts 404, and any set that would close a dependency cycle 409."""
    return concept_graph_service.set_concept_prerequisites(
        db, concept_id, payload.prerequisite_concept_ids
    )


# ---------- UC20 — cohort analytics & learner drill-down (DBCAS-25) ----------


@router.get("/analytics/cohort", response_model=CohortOverviewResult)
def cohort_overview(
    assessment_id: Optional[int] = None,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Cohort-wide per-concept standing: averages, below-benchmark counts,
    and gap prevalence over each learner's latest finalized result."""
    return analytics_service.cohort_overview(db, assessment_id)


@router.get("/learners", response_model=list[AdminLearnerItem])
def list_learners(
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Learner roster with activity counts for the drill-down picker."""
    return analytics_service.list_learners(db)


@router.get(
    "/learners/{account_id}/sessions",
    response_model=AdminLearnerSessionsResult,
)
def learner_sessions(
    account_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """One learner's assessment history (404 for non-learner ids)."""
    return analytics_service.learner_sessions(db, account_id)


@router.get(
    "/sessions/{session_id}/competency",
    response_model=CompetencyProfileResult,
)
def admin_session_competency(
    session_id: int,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """Per-learner radar data: the same deterministic competency profile
    the learner sees, without the ownership restriction."""
    return analytics_service.session_competency(db, session_id)
