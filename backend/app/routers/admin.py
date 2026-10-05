from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import AdminOnly
from ..models import Account
from ..schemas import (
    AccountSummary,
    ConceptPrerequisitesResult,
    ProvisionAccountRequest,
    SetPrerequisitesRequest,
)
from ..services import auth_service, concept_graph_service

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
