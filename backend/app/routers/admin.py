from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import AdminOnly
from ..models import Account
from ..schemas import AccountSummary, ProvisionAccountRequest
from ..services import auth_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/accounts", status_code=201, response_model=AccountSummary)
def provision_account(
    payload: ProvisionAccountRequest,
    _: Account = AdminOnly,
    db: Session = Depends(get_db),
):
    """UC04 — Administrator provisions a new account (starts disabled)."""
    return auth_service.provision_account(db, payload)
