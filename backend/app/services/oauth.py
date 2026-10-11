"""Social sign-in: Google + GitHub OAuth 2.0 authorization-code flows.

Backend-managed flow (UC02 extension):

    SPA button
      → GET /auth/oauth/{provider}/start      (302 to the provider, sets
        HttpOnly state + PKCE-verifier cookies)
      → provider authorization
      → GET /auth/oauth/{provider}/callback   (verifies state, exchanges
        the code server-side, resolves/links the account, sets a
        short-lived HttpOnly handoff cookie)
      → 302 to the SPA /auth/callback
      → POST /auth/oauth/complete             (SPA exchanges the handoff
        cookie for the normal Bearer JWT)

Security model:

- ``state`` is a signed JWT (provider + nonce + exp) mirrored in an
  HttpOnly ``SameSite=Lax`` cookie. The callback requires cookie value ==
  query param, which binds the flow to the browser that started it —
  the standard login-CSRF countermeasure for server-side OAuth.
- PKCE (S256) is used on the Google flow; the verifier lives in its own
  HttpOnly cookie so it never appears in any URL. GitHub's app flow is
  client-secret based, so PKCE is not sent there.
- Provider access tokens are used once, server-side, to fetch the profile
  and are never persisted or exposed to the browser. The SPA receives the
  normal DBCAS JWT only through the one-time handoff cookie + POST
  exchange — no tokens in URLs.
- Account resolution never grants or changes roles: an existing
  ``account_identity`` link wins; otherwise a *provider-verified* email
  links to a matching account; otherwise a new active Learner is created.
  Unverified/absent provider emails can never attach to an account.
- Handoff JWTs carry a distinct purpose and have a hashed database record.
  Atomic consume makes them single-use across processes and deployments.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWTError as JWTError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Account
from ..repositories import AccountRepository
from ..security import hash_password

STATE_COOKIE = "dbcas_oauth_state"
VERIFIER_COOKIE = "dbcas_oauth_verifier"
HANDOFF_COOKIE = "dbcas_oauth_handoff"
COOKIE_PATH = "/api/v1/auth/oauth"

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


class OAuthFlowError(Exception):
    """A callback-stage failure; ``code`` becomes ?oauth_error=<code> on
    the SPA redirect so the login page can render a friendly message."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    authorize_url: str
    token_url: str
    scope: str
    use_pkce: bool
    client_id: str
    client_secret: str
    redirect_uri: str

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.redirect_uri)


@dataclass(frozen=True)
class ProviderIdentity:
    provider: str
    provider_user_id: str
    email: Optional[str]
    email_verified: bool
    name: Optional[str]


def get_provider(settings: Settings, name: str) -> Optional[ProviderSpec]:
    """Provider spec, or None for an unknown provider name."""
    if name == "google":
        return ProviderSpec(
            name="google",
            authorize_url=GOOGLE_AUTHORIZE_URL,
            token_url=GOOGLE_TOKEN_URL,
            scope="openid email profile",
            use_pkce=True,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=settings.google_redirect_uri,
        )
    if name == "github":
        return ProviderSpec(
            name="github",
            authorize_url=GITHUB_AUTHORIZE_URL,
            token_url=GITHUB_TOKEN_URL,
            scope="read:user user:email",
            use_pkce=False,
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            redirect_uri=settings.github_redirect_uri,
        )
    return None


def provider_statuses(settings: Settings) -> list[dict]:
    """Which providers can actually complete a flow — public metadata the
    login page uses to disable unconfigured buttons (no secrets)."""
    return [
        {"name": name, "configured": spec.configured}
        for name in ("google", "github")
        if (spec := get_provider(settings, name)) is not None
    ]


# ---------- state (CSRF binding) ----------


def issue_state(provider: str, settings: Settings) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "purpose": "oauth_state",
            "provider": provider,
            "nonce": secrets.token_urlsafe(16),
            "iat": now,
            "exp": now + settings.oauth_state_ttl_seconds,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def verify_state(state: str, provider: str, settings: Settings) -> bool:
    try:
        payload = jwt.decode(
            state, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return False
    return (
        payload.get("purpose") == "oauth_state"
        and payload.get("provider") == provider
        and bool(payload.get("nonce"))
    )


def new_pkce() -> tuple[str, str]:
    """RFC 7636 — (code_verifier, S256 code_challenge)."""
    verifier = secrets.token_urlsafe(48)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    return verifier, challenge


def authorize_url(spec: ProviderSpec, state: str, challenge: str = "") -> str:
    params = {
        "response_type": "code",
        "client_id": spec.client_id,
        "redirect_uri": spec.redirect_uri,
        "scope": spec.scope,
        "state": state,
    }
    if challenge:
        params["code_challenge"] = challenge
        params["code_challenge_method"] = "S256"
    return f"{spec.authorize_url}?{urlencode(params)}"


def cookie_secure(settings: Settings) -> bool:
    return settings.frontend_url.startswith("https://")


def frontend_url(settings: Settings) -> str:
    return settings.frontend_url.rstrip("/")


# ---------- handoff (single-use, no tokens in URLs) ----------

def issue_handoff(account_id: int, provider: str, settings: Settings, db: Session) -> tuple[str, int]:
    """Returns (handoff_jwt, ttl_seconds)."""
    now = int(time.time())
    ttl = settings.oauth_handoff_ttl_seconds
    jti = secrets.token_urlsafe(32)
    token = jwt.encode(
        {
            "purpose": "oauth_handoff",
            "typ": "oauth_handoff",
            "jti": jti,
            "sub": str(account_id),
            "provider": provider,
            "iat": now,
            "exp": now + ttl,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    from ..repositories import SecurityRepository
    repo = SecurityRepository(db)
    repo.prune_handoffs()
    repo.store_handoff(jti, account_id, datetime.fromtimestamp(now + ttl, timezone.utc))
    db.commit()
    return token, ttl


def consume_handoff(token: str, settings: Settings, db: Session) -> int:
    """Verify the handoff JWT and burn its jti — one use per flow."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        raise OAuthFlowError("complete")
    if payload.get("typ") != "oauth_handoff" or payload.get("purpose") != "oauth_handoff" or not payload.get("sub") or not payload.get("exp"):
        raise OAuthFlowError("complete")
    jti = payload.get("jti")
    try:
        account_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise OAuthFlowError("complete")
    if not isinstance(jti, str) or not jti:
        raise OAuthFlowError("complete")
    from ..repositories import SecurityRepository
    consumed = SecurityRepository(db).consume_handoff(jti, account_id)
    db.commit()
    if consumed is None:
        raise OAuthFlowError("complete")
    return consumed


# ---------- provider calls ----------


def _normalize_email(email: Optional[str]) -> Optional[str]:
    if email is None:
        return None
    if not isinstance(email, str):
        raise OAuthFlowError("profile")
    email = email.strip().lower()
    if email:
        from ..schemas import _validate_email
        try:
            email = _validate_email(email)
        except ValueError:
            raise OAuthFlowError("profile") from None
    return email or None


def _profile_name(value):
    if value is not None and not isinstance(value, str):
        raise OAuthFlowError("profile")
    if not value:
        return None
    return value.strip()[:100] or None


def _exchange_code(
    spec: ProviderSpec, code: str, verifier: str, http: httpx.Client
) -> str:
    """Authorization code → provider access token (server-side only)."""
    form = {
        "client_id": spec.client_id,
        "client_secret": spec.client_secret,
        "code": code,
        "redirect_uri": spec.redirect_uri,
        "grant_type": "authorization_code",
    }
    if verifier:
        form["code_verifier"] = verifier
    try:
        resp = http.post(
            spec.token_url,
            data=form,
            headers={"Accept": "application/json"},
        )
        body = resp.json()
    except (httpx.HTTPError, ValueError):
        raise OAuthFlowError("exchange")
    if resp.status_code != 200 or not isinstance(body, dict):
        raise OAuthFlowError("exchange")
    token = body.get("access_token")
    if not isinstance(token, str) or not token or len(token) > 4096 or any(c.isspace() for c in token):
        raise OAuthFlowError("exchange")
    return token


def _google_identity(spec: ProviderSpec, access_token: str, http: httpx.Client) -> ProviderIdentity:
    try:
        resp = http.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        body = resp.json()
    except (httpx.HTTPError, ValueError):
        raise OAuthFlowError("profile")
    if resp.status_code != 200 or not isinstance(body, dict) or not isinstance(body.get("sub"), str) or not body["sub"].strip() or len(body["sub"]) > 255:
        raise OAuthFlowError("profile")
    return ProviderIdentity(
        provider=spec.name,
        provider_user_id=str(body["sub"]),
        email=_normalize_email(body.get("email")),
        email_verified=body.get("email_verified") is True,
        name=_profile_name(body.get("name")),
    )


def _github_identity(spec: ProviderSpec, access_token: str, http: httpx.Client) -> ProviderIdentity:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }
    try:
        user_resp = http.get(GITHUB_USER_URL, headers=headers)
        user = user_resp.json()
    except (httpx.HTTPError, ValueError):
        raise OAuthFlowError("profile")
    if user_resp.status_code != 200 or not isinstance(user, dict) or type(user.get("id")) is not int or user["id"] <= 0:
        raise OAuthFlowError("profile")

    # Only /user/emails entries carry a `verified` flag — the public email
    # on /user is user-supplied and unsafe to link on. Always consult it.
    email = verified = None
    try:
        emails_resp = http.get(GITHUB_EMAILS_URL, headers=headers)
        emails = emails_resp.json()
    except (httpx.HTTPError, ValueError):
        raise OAuthFlowError("profile") from None
    if emails_resp.status_code != 200 or not isinstance(emails, list):
        raise OAuthFlowError("profile")
    if emails_resp.status_code == 200 and isinstance(emails, list):
        primaries = [e for e in emails if isinstance(e, dict) and e.get("primary") is True and e.get("verified") is True]
        verified_any = [e for e in emails if isinstance(e, dict) and e.get("verified") is True]
        chosen = primaries[0] if primaries else (verified_any[0] if verified_any else None)
        if chosen:
            email = _normalize_email(chosen.get("email"))
            verified = True
    return ProviderIdentity(
        provider=spec.name,
        provider_user_id=str(user["id"]),
        email=email,
        email_verified=verified is True,
        name=_profile_name(user.get("name")) or _profile_name(user.get("login")),
    )


def fetch_identity(
    spec: ProviderSpec, code: str, verifier: str, http: httpx.Client
) -> ProviderIdentity:
    access_token = _exchange_code(spec, code, verifier, http)
    if spec.name == "google":
        return _google_identity(spec, access_token, http)
    return _github_identity(spec, access_token, http)


# ---------- account resolution ----------


def resolve_or_create(db: Session, ident: ProviderIdentity) -> Account:
    """Map a provider identity to a local account.

    Order: existing identity link → verified-email match (writes a link)
    → new active Learner. Roles are never taken from provider data, so a
    social login can neither create an admin nor escalate one."""
    repo = AccountRepository(db)
    # Lock both subject and normalized email in a stable order. The unique
    # indexes remain the final authority, including races with registration.
    from ..repositories import SecurityRepository
    for key in sorted({f"oauth:{ident.provider}:{ident.provider_user_id}", f"email:{_normalize_email(ident.email) or '-'}"}):
        SecurityRepository(db).lock(key)

    existing = repo.find_identity(ident.provider, ident.provider_user_id)
    if existing is not None:
        account = existing.account
        if account.status != "active":
            raise OAuthFlowError("account_disabled")
        return account

    if not ident.email or not ident.email_verified:
        raise OAuthFlowError("email_unverified")

    try:
        account = repo.find_by_email(ident.email)
        if account is None:
            account = repo.create_learner(
                email=ident.email,
                password_hash=hash_password(secrets.token_urlsafe(48)),
                full_name=(ident.name or ident.email.split("@")[0])[:100],
            )
            db.flush()
        if account.status != "active":
            raise OAuthFlowError("account_disabled")
        repo.link_identity(account.account_id, ident.provider, ident.provider_user_id,
                           ident.email, ident.email_verified)
        db.commit()
        db.refresh(account)
        return account
    except IntegrityError:
        db.rollback()
        # Registration can race with OAuth outside the subject/email locks.
        # Reload only the authoritative link, or attach the winning email
        # account under the same locks; never return an arbitrary loser.
        existing = repo.find_identity(ident.provider, ident.provider_user_id)
        if existing is not None:
            if existing.account.status != "active":
                raise OAuthFlowError("account_disabled")
            return existing.account
        account = repo.find_by_email(ident.email)
        if account is None or account.status != "active":
            raise OAuthFlowError("exchange")
        try:
            repo.link_identity(account.account_id, ident.provider, ident.provider_user_id,
                               ident.email, ident.email_verified)
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = repo.find_identity(ident.provider, ident.provider_user_id)
            if existing is None or existing.account_id != account.account_id:
                raise OAuthFlowError("exchange")
        return account
