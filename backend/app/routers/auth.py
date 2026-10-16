from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..db import get_db
from ..deps import CurrentAccount
from ..errors import AppError
from ..models import Account
from ..schemas import AccountSummary, LoginRequest, RegisterRequest, TokenResponse
from ..services import auth_service
from ..security import decode_access_token, create_access_token
from ..services.login_throttle import LoginThrottle, DatabaseLoginThrottle, get_login_throttle

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=AccountSummary)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """UC01 — learner self-registration (always the Learner role)."""
    return auth_service.register_learner(db, payload)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    throttle: LoginThrottle = Depends(get_login_throttle),
):
    """UC02 — verify credentials + active status, issue a JWT.

    Failed-credential attempts are throttled per (email, client_ip);
    success resets the window. The check runs before verification so a
    saturated window caps all further attempts within it.
    """
    client_ip = request.client.host if request.client else None
    if settings.deployment_mode != "development":
        throttle = DatabaseLoginThrottle(db)
    key = throttle.key(payload.email, client_ip)
    with throttle.transaction(key):
        throttle.check(key, settings)
        try:
            token, expires_in, account = auth_service.login(db, payload, settings)
        except AppError as e:
            if e.code == "invalid_credentials":
                throttle.record_failure(key, settings)
            raise
        throttle.record_success(key)
    return TokenResponse(
        access_token=token, expires_in=expires_in, account=account
    )


@router.get("/me", response_model=AccountSummary)
def me(account: Account = CurrentAccount):
    """Current authenticated account — used by the SPA after login."""
    return auth_service.to_summary(account)


@router.post("/renew", response_model=TokenResponse)
def renew_access_token(request: Request, account: Account = CurrentAccount, settings: Settings = Depends(get_settings)):
    """Renew a still-valid access session, with an absolute sign-in lifetime."""
    claims = decode_access_token(request.headers["authorization"].removeprefix("Bearer ").strip(), settings)
    auth_time = claims.get("auth_time", claims.get("iat"))
    if type(auth_time) is not int:
        raise AppError(401, "invalid_token", "Token is missing its sign-in time")
    token, expires_in = create_access_token(account.account_id, sorted(r.role_name for r in account.roles), settings, auth_time=auth_time)
    return TokenResponse(access_token=token, expires_in=expires_in, account=auth_service.to_summary(account))
