from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..db import get_db
from ..deps import CurrentAccount
from ..models import Account
from ..schemas import AccountSummary, LoginRequest, RegisterRequest, TokenResponse
from ..services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=AccountSummary)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """UC01 — learner self-registration (always the Learner role)."""
    return auth_service.register_learner(db, payload)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """UC02 — verify credentials + active status, issue a JWT."""
    token, expires_in, account = auth_service.login(db, payload, settings)
    return TokenResponse(
        access_token=token, expires_in=expires_in, account=account
    )


@router.get("/me", response_model=AccountSummary)
def me(account: Account = CurrentAccount):
    """Current authenticated account — used by the SPA after login."""
    return auth_service.to_summary(account)
