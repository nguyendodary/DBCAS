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
- Handoff JWTs are single-use (consumed JTIs are kept for their TTL).
  In-memory like LoginThrottle — per-process, fine for this deployment
  shape; a multi-replica deployment should move it to shared storage.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt
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

_consumed_jti: dict[str, float] = {}


def issue_handoff(account_id: int, provider: str, settings: Settings) -> tuple[str, int]:
    """Returns (handoff_jwt, ttl_seconds)."""
    now = int(time.time())
    ttl = settings.oauth_handoff_ttl_seconds
    token = jwt.encode(
        {
            "purpose": "oauth_handoff",
            "jti": secrets.token_urlsafe(16),
            "sub": str(account_id),
            "provider": provider,
            "iat": now,
            "exp": now + ttl,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token, ttl


def consume_handoff(token: str, settings: Settings) -> int:
    """Verify the handoff JWT and burn its jti — one use per flow."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        raise OAuthFlowError("complete")
    if payload.get("purpose") != "oauth_handoff" or not payload.get("sub"):
        raise OAuthFlowError("complete")
    jti = payload.get("jti")
    now = time.time()
    for key, exp in list(_consumed_jti.items()):
        if exp <= now:
            _consumed_jti.pop(key, None)
    if not jti or jti in _consumed_jti:
        raise OAuthFlowError("complete")
    _consumed_jti[jti] = now + settings.oauth_handoff_ttl_seconds
    try:
        return int(payload["sub"])
    except (TypeError, ValueError):
        raise OAuthFlowError("complete")


# ---------- provider calls ----------


def _normalize_email(email: Optional[str]) -> Optional[str]:
    email = (email or "").strip().lower()
    return email or None


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
    if resp.status_code != 200 or not isinstance(body, dict) or not body.get("access_token"):
        raise OAuthFlowError("exchange")
    return str(body["access_token"])


def _google_identity(spec: ProviderSpec, access_token: str, http: httpx.Client) -> ProviderIdentity:
    try:
        resp = http.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        body = resp.json()
    except (httpx.HTTPError, ValueError):
        raise OAuthFlowError("profile")
    if resp.status_code != 200 or not isinstance(body, dict) or not body.get("sub"):
        raise OAuthFlowError("profile")
    return ProviderIdentity(
        provider=spec.name,
        provider_user_id=str(body["sub"]),
        email=_normalize_email(body.get("email")),
        email_verified=body.get("email_verified") is True,
        name=body.get("name") or None,
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
    if user_resp.status_code != 200 or not isinstance(user, dict) or not user.get("id"):
        raise OAuthFlowError("profile")

    # Only /user/emails entries carry a `verified` flag — the public email
    # on /user is user-supplied and unsafe to link on. Always consult it.
    email = verified = None
    try:
        emails_resp = http.get(GITHUB_EMAILS_URL, headers=headers)
        emails = emails_resp.json()
    except (httpx.HTTPError, ValueError):
        emails = None
    if emails_resp.status_code == 200 and isinstance(emails, list):
        primaries = [e for e in emails if e.get("primary") and e.get("verified")]
        verified_any = [e for e in emails if e.get("verified")]
        chosen = primaries[0] if primaries else (verified_any[0] if verified_any else None)
        if chosen:
            email = _normalize_email(chosen.get("email"))
            verified = True
    return ProviderIdentity(
        provider=spec.name,
        provider_user_id=str(user["id"]),
        email=email,
        email_verified=verified is True,
        name=user.get("name") or user.get("login") or None,
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

    existing = repo.find_identity(ident.provider, ident.provider_user_id)
    if existing is not None:
        account = existing.account
        if account.status != "active":
            raise OAuthFlowError("account_disabled")
        return account

    if not ident.email or not ident.email_verified:
        raise OAuthFlowError("email_unverified")

    account = repo.find_by_email(ident.email)
    if account is None:
        # Social accounts get a random unguessable password hash — password
        # sign-in stays possible only after a real password is set through
        # a future reset flow; OAuth is the only way in until then.
        account = repo.create_learner(
            email=ident.email,
            password_hash=hash_password(secrets.token_urlsafe(48)),
            full_name=(ident.name or ident.email.split("@")[0])[:100],
        )
        db.flush()  # account_id is needed for the identity row below
        try:
            repo.link_identity(
                account.account_id,
                ident.provider,
                ident.provider_user_id,
                ident.email,
                ident.email_verified,
            )
            db.commit()
        except IntegrityError:
            db.rollback()
            # Concurrent flow already linked/created — fall back to lookup.
            existing = repo.find_identity(ident.provider, ident.provider_user_id)
            if existing is None or existing.account.status != "active":
                raise OAuthFlowError("exchange")
            return existing.account
        db.refresh(account)
        return account

    if account.status != "active":
        raise OAuthFlowError("account_disabled")
    try:
        repo.link_identity(
            account.account_id,
            ident.provider,
            ident.provider_user_id,
            ident.email,
            ident.email_verified,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
    db.refresh(account)
    return account
