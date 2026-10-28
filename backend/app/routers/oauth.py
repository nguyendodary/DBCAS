"""Social sign-in routes — see services/oauth.py for the flow and its
security model. Handlers stay thin: provider lookup, cookie plumbing,
and mapping OAuthFlowError codes onto SPA redirects."""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..db import get_db
from ..errors import AppError
from ..repositories import AccountRepository
from ..schemas import TokenResponse
from ..security import create_access_token
from ..services import auth_service, oauth

router = APIRouter(prefix="/auth/oauth", tags=["auth"])


def get_http_client() -> httpx.Client:
    """Injectable so tests can substitute a MockTransport client — the
    suite never makes real provider calls."""
    return httpx.Client(timeout=10.0)


def _spec_or_error(settings: Settings, provider: str) -> oauth.ProviderSpec:
    spec = oauth.get_provider(settings, provider)
    if spec is None:
        raise AppError(404, "oauth_unknown_provider", "Unknown OAuth provider")
    if not spec.configured:
        raise AppError(
            503,
            "oauth_not_configured",
            f"{provider} sign-in is not configured on this server",
        )
    return spec


def _login_redirect(settings: Settings, code: str) -> RedirectResponse:
    return RedirectResponse(
        f"{oauth.frontend_url(settings)}/login?oauth_error={code}",
        status_code=302,
    )


def _set_flow_cookie(
    resp: Response, name: str, value: str, settings: Settings, max_age: int
) -> None:
    resp.set_cookie(
        name,
        value,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=oauth.cookie_secure(settings),
        path=oauth.COOKIE_PATH,
    )


@router.get("/providers")
def providers(settings: Settings = Depends(get_settings)):
    """Public list of configured providers — the SPA disables buttons for
    unconfigured ones instead of sending users into a dead flow."""
    return {"providers": oauth.provider_statuses(settings)}


@router.get("/{provider}/start")
def start(provider: str, settings: Settings = Depends(get_settings)):
    """Begin the authorization-code flow: 302 to the provider with a
    signed state (mirrored in an HttpOnly cookie) and optional PKCE."""
    spec = _spec_or_error(settings, provider)
    state = oauth.issue_state(provider, settings)
    verifier, challenge = oauth.new_pkce() if spec.use_pkce else ("", "")
    resp = RedirectResponse(
        oauth.authorize_url(spec, state, challenge), status_code=302
    )
    _set_flow_cookie(
        resp, oauth.STATE_COOKIE, state, settings, settings.oauth_state_ttl_seconds
    )
    if verifier:
        _set_flow_cookie(
            resp,
            oauth.VERIFIER_COOKIE,
            verifier,
            settings,
            settings.oauth_state_ttl_seconds,
        )
    return resp


@router.get("/{provider}/callback")
def callback(
    provider: str,
    request: Request,
    code: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    error: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    http: httpx.Client = Depends(get_http_client),
):
    """Provider redirect target. Every failure returns to the login page
    with an error code — failures never create sessions or accounts."""
    spec = oauth.get_provider(settings, provider)
    if spec is None:
        raise AppError(404, "oauth_unknown_provider", "Unknown OAuth provider")

    def fail(code_: str) -> RedirectResponse:
        resp = _login_redirect(settings, code_)
        resp.delete_cookie(oauth.STATE_COOKIE, path=oauth.COOKIE_PATH)
        resp.delete_cookie(oauth.VERIFIER_COOKIE, path=oauth.COOKIE_PATH)
        return resp

    if error is not None:
        return fail("denied")
    if not spec.configured:
        return fail("not_configured")
    cookie_state = request.cookies.get(oauth.STATE_COOKIE)
    verifier = request.cookies.get(oauth.VERIFIER_COOKIE, "")
    if (
        not state
        or not cookie_state
        or cookie_state != state
        or not oauth.verify_state(state, provider, settings)
    ):
        return fail("state")
    if not code:
        return fail("denied")

    try:
        ident = oauth.fetch_identity(spec, code, verifier, http)
    except oauth.OAuthFlowError as e:
        return fail(e.code)

    try:
        account = oauth.resolve_or_create(db, ident)
    except oauth.OAuthFlowError as e:
        return fail(e.code)

    handoff, ttl = oauth.issue_handoff(account.account_id, provider, settings, db)
    resp = RedirectResponse(
        f"{oauth.frontend_url(settings)}/auth/callback", status_code=302
    )
    resp.delete_cookie(oauth.STATE_COOKIE, path=oauth.COOKIE_PATH)
    resp.delete_cookie(oauth.VERIFIER_COOKIE, path=oauth.COOKIE_PATH)
    _set_flow_cookie(resp, oauth.HANDOFF_COOKIE, handoff, settings, ttl)
    return resp


@router.post("/complete", response_model=TokenResponse)
def complete(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Exchange the one-time handoff cookie for the normal Bearer JWT.

    The handoff JWT is single-use and short-lived; the SPA calls this from
    /auth/callback so no token ever travels in a URL."""
    token = request.cookies.get(oauth.HANDOFF_COOKIE)
    try:
        if not token:
            raise oauth.OAuthFlowError("complete")
        account_id = oauth.consume_handoff(token, settings, db)
    except oauth.OAuthFlowError:
        raise AppError(401, "oauth_handoff_invalid", "Sign-in handoff is invalid or expired")

    account = AccountRepository(db).get_with_roles(account_id)
    if account is None or account.status != "active":
        raise AppError(403, "account_disabled", "Account is not active")
    roles = sorted(r.role_name for r in account.roles)
    access_token, expires_in = create_access_token(
        account.account_id, roles, settings,
        password_changed_at=account.password_changed_at,
    )
    response.delete_cookie(oauth.HANDOFF_COOKIE, path=oauth.COOKIE_PATH)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        account=auth_service.to_summary(account),
    )
