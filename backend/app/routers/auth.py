from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..db import get_db
from ..deps import CurrentAccount
from ..errors import AppError
from ..models import Account
from ..schemas import (
    AccountSummary,
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
)
from ..services import auth_service, password_reset
from ..services.mail import Mailer
from ..security import decode_access_token, create_access_token
from ..services.login_throttle import (
    DatabaseLoginThrottle,
    DatabasePasswordResetThrottle,
    LoginThrottle,
    get_login_throttle,
    get_password_reset_throttle,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_mailer(settings: Settings = Depends(get_settings)) -> Mailer:
    """Injectable so tests can capture messages without a live SMTP server."""
    return Mailer(settings)


def _reset_policy(settings: Settings, attempts: int) -> Settings:
    """LoginThrottle reads its policy from these two fields; a copy applies
    password-reset limits without duplicating the limiter implementation."""
    return settings.model_copy(
        update={
            "login_rate_limit_attempts": attempts,
            "login_rate_limit_window_seconds": settings.password_reset_rate_limit_window_seconds,
        }
    )


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


@router.post("/password-reset/request", status_code=202)
def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    throttle: LoginThrottle = Depends(get_password_reset_throttle),
    mailer: Mailer = Depends(get_mailer),
):
    """Start self-service recovery (dev inbox: Mailpit at 127.0.0.1:8026).

    A syntactically valid email always receives 202 with the same body, so
    the response cannot be used to enumerate known, unknown or disabled
    accounts. The message itself is only queued for active accounts, and
    delivery runs after the response so SMTP latency is not observable.
    """
    if not mailer.configured:
        raise AppError(
            503,
            "password_reset_unavailable",
            "Password reset email is not configured on this server",
        )
    client_ip = request.client.host if request.client else None
    if settings.deployment_mode != "development":
        throttle = DatabasePasswordResetThrottle(db)
    for key, view in (
        (
            throttle.key("reset:" + payload.email, client_ip),
            _reset_policy(settings, settings.password_reset_rate_limit_attempts),
        ),
        (
            throttle.key("reset-ip:" + (client_ip or "-"), client_ip),
            _reset_policy(settings, settings.password_reset_ip_rate_limit_attempts),
        ),
    ):
        with throttle.transaction(key):
            throttle.check(key, view)
            # Every request consumes quota — unknown addresses included.
            throttle.record_failure(key, view)
    issued = password_reset.request_reset(db, payload.email, settings)
    if issued is not None:
        token, email = issued
        reset_url = f"{settings.frontend_url.rstrip('/')}/reset-password?token={token}"
        background_tasks.add_task(
            mailer.send_password_reset,
            email,
            reset_url,
            settings.password_reset_token_ttl_minutes,
        )
    return {"status": "accepted"}


@router.post("/password-reset/confirm")
def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    throttle: LoginThrottle = Depends(get_password_reset_throttle),
):
    """Redeem a single-use reset token and set the new password.

    The token is consumed under a row lock; success invalidates every
    outstanding session (``pwd_at`` claim) and every other live reset token.
    """
    client_ip = request.client.host if request.client else None
    if settings.deployment_mode != "development":
        throttle = DatabasePasswordResetThrottle(db)
    key = throttle.key("reset-confirm-ip:" + (client_ip or "-"), client_ip)
    view = _reset_policy(settings, settings.password_reset_confirm_rate_limit_attempts)
    with throttle.transaction(key):
        throttle.check(key, view)
        throttle.record_failure(key, view)
    password_reset.confirm_reset(db, payload)
    return {"status": "reset"}


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
    token, expires_in = create_access_token(
        account.account_id, sorted(r.role_name for r in account.roles), settings,
        auth_time=auth_time, password_changed_at=account.password_changed_at,
    )
    return TokenResponse(access_token=token, expires_in=expires_in, account=auth_service.to_summary(account))
