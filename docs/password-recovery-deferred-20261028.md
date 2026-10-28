# Password recovery: why self-service reset is deferred — 28 October 2026

## Defect

Remote commit `aa03a97` ("feat(frontend): align main auth and landing UI") added a
"Forgot password?" link to the login card (`frontend/src/pages/LoginPage.jsx`, previously
line 105) pointing at `/forgot-password`. The SPA has no such route; `App.jsx`'s catch-all
(`<Route path="*" element={<Navigate to="/" replace />} />`) silently redirected users to the
landing page. The link promised a capability the product does not have.

## What the codebase does and does not contain

| Building block of a real recovery flow | Present? | Evidence |
|---|---|---|
| Reset request / confirm API endpoints | **no** | `backend/app/routers/auth.py` exposes only `/auth/register`, `/auth/login`, `/auth/me`, `/auth/renew` |
| Reset-token storage (table, expiry, single use) | **no** | no token table among the 35 tables in `db/schema.sql`; no reset service in `app/services/` |
| Email delivery (SMTP/SES/provider, templates, retries) | **no** | no mail library in `backend/requirements.txt`, no mail settings in `.env.example` or `app/config.py`, no sender code |
| Administrator-issued reset | **no** | no password/credential action in `backend/app/routers/admin.py` |
| Password hashing and policy (reusable for a reset) | yes | bcrypt `hash_password`/`verify_password` in `app/services/auth_service.py`; `_validate_password` in `app/schemas.py` |
| Login throttling abstraction (reusable) | yes | `app/services/login_throttle.py` |

A genuine flow — request page, emailed short-lived single-use token, reset page, session
invalidation, no user enumeration, rate limiting — would require new email infrastructure,
a schema migration, new endpoints and a full security review. Without an email channel the
request step cannot deliver a link at all, so shipping the UI first would reproduce exactly
the defect being fixed: a working-looking page that cannot send anything.

## Decision

Remove the link rather than fake the feature. The login page now renders only controls that
work: email/password sign-in, Google/GitHub OAuth (server-driven availability), and the
register link. The unused `auth.forgotPassword` keys (`en.json`, `vi.json`) and the orphaned
`.auth-forgot-link` CSS rules were removed with it. If a user asks for recovery today, the
honest answer is that the deployment has no self-service reset; an administrator can still
provision or update accounts through the existing account management surface.

Regression coverage: `frontend/src/test/AuthPages.test.jsx` asserts the login page renders no
"Forgot password?" link and no `a[href="/forgot-password"]`, alongside the existing login,
redirect, error and OAuth tests. The localization test keeps EN/VI key sets identical.

## If recovery is implemented later

It must ship as one unit: provider-backed email with a verified sender; a reset-token table
(hashed token, expiry, single-use, revoked on use); endpoints that respond identically for
known and unknown emails; request throttling (reusing `login_throttle`); token invalidation
and session invalidation after reset; password policy reuse; accessible EN/VI pages; and
tests for valid, expired, reused, invalid and abused requests. Tokens and passwords must
never be logged or returned in responses.
