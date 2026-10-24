# Staging/production deployment and readiness

This guide defines a local/reviewable deployment path; it does not authorize
publishing or deploying to an external service. Use an HTTPS gateway in front
of the release stack. The frontend and API must share the public origin.

## Private configuration

Copy `deploy/release.env.example` to the ignored `deploy/.env`, then replace
every placeholder. Never commit or print that file. Use distinct random app
DB, sandbox administrator and sandbox learner passwords of at least 16
characters; use a random JWT secret of at least 32 bytes. Prefer a password
manager or cryptographic secret generator. Do not use public development
credentials or example values.

Set `DEPLOYMENT_MODE=staging` or `production`, `JWT_ALGORITHM=HS256`, a public
HTTPS `FRONTEND_URL` and explicit matching HTTPS `CORS_ORIGINS`. Wildcards,
development/placeholder JWT secrets, default DB passwords and sandbox/app DB
server reuse fail configuration validation. An active seeded development
password also fails application startup. Errors identify keys, not values.

Container URLs use `db:5432` for the app database and `sandbox:5432` for
the separate sandbox. URL-encode special password characters in DSNs.
The example's `DBCAS_RELEASE_ENV_FILE=deploy/.env` is relative to this repo.
Choose the host HTTP port with `DBCAS_RELEASE_HTTP_PORT`; it binds localhost
only. The HTTPS gateway should forward to that port. Register exact public
OAuth callback URLs with Google/GitHub, using `/api/v1/auth/oauth/...` under
the UI origin. Provider secrets remain backend environment variables.

Access JWTs last 60 minutes by default and have explicit access purpose.
Renewal retains original authentication time, with an eight-hour absolute
window by default. Handoff/state tokens cannot be used as access tokens.
Handoffs are hashed, expiring, atomically consumed database records shared
by workers. Production login throttling likewise uses shared atomic DB state.

## Start the standalone release stack

Run from the repository root. It uses its own project/volume and never
combines with the development Compose file.

```powershell
docker compose --env-file deploy/.env -f docker-compose.release.yml config -q
docker compose --env-file deploy/.env -f docker-compose.release.yml up -d --build
docker compose --env-file deploy/.env -f docker-compose.release.yml ps
```

The database initializes fresh DDL without the development account seed.
The one-shot migrate service applies additive, checksum-verified migrations
before the backend starts. Existing release volumes use the same migration
path. Keep backups under the operator's normal retention policy. Never use
`down -v`, database reset, pruning, or deletion as an upgrade mechanism.

The backend runs Python 3.13 as a nonroot user with two API workers. SQL
execution uses the separate 256 MB/one-CPU sandbox, no outbound network or
application DB network, a minimal read-only learner role and isolated setup
schemas. Only the frontend publishes a host HTTP port; no app/sandbox DB
port is published. Nginx serves hashed static assets, SPA routes and `/api`,
with CSP and basic security headers. Fonts are self-hosted under OFL licenses.
The backend web network permits outbound provider HTTP when configured.

After migration, create the first trusted Administrator interactively:

```powershell
docker compose --env-file deploy/.env -f docker-compose.release.yml run --rm backend python -m app.bootstrap_admin --email owner@example.edu --name "Deployment owner"
```

The CLI reads/confirm the password using a hidden prompt, never command-line
password arguments. It rejects the public seed password, duplicate email or
any existing Administrator. The initial trusted Administrator receives the
separate role-management capability and is recorded in the audit table.
Existing installations with an Administrator but no configured role manager
must provision exactly one through the explicit account-ID operator command
in the setup guide. Later role changes and Administrator provisioning are
restricted to role managers; ordinary Administrators retain other admin
features without receiving role-assignment authority.
Import the reviewed benchmark with this administrator if required; see the
setup/migration guide. Do not reuse development learner records in production.

## AI execution and bounded retries

Set `LLM_BASE_URL`, `LLM_MODEL` and `LLM_API_KEY` for an OpenAI-compatible
chat-completions endpoint. The endpoint suffix is handled by the provider
adapter. Use temperature 0.1 (or a lower deterministic setting), seed 42,
finite timeout and bounded retries. Responses pass strict JSON/schema/domain
validation before entering the versioned cache. Learner profile identifiers
are redacted with boundaries; AI cannot change deterministic competency math.

The API maintenance thread handles timeouts and pending SQL jobs. Essay
retry jobs require an explicit operator decision to enable provider calls:

```powershell
docker compose --env-file deploy/.env -f docker-compose.release.yml --profile ai-worker up -d worker
```

This profile intentionally contains `--allow-provider-calls` and can incur
provider charges. Do not enable it during automated gates. Without a provider,
essay submissions may remain explicitly pending; do not describe this mode
as full assessment readiness. Jobs have bounded attempts, leases and safe
failure state; monitor failed grades and investigate provider configuration.

## Operational checks

`GET /health` is process liveness. `GET /readiness` returns 200 only when
the required app schema and sandbox connection are usable; otherwise 503
with dependency booleans and no connection details. The release backend's
container health check uses readiness. Ensure the HTTPS gateway has its own
readiness and certificate checks. Test a learner's complete assessment and
both configured OAuth sign-ins after changing security/deployment settings.

Application connections default to `DATABASE_CONNECT_TIMEOUT_SECONDS=5`
and pool acquisition to `DATABASE_POOL_TIMEOUT_SECONDS=5`. Readiness uses
a fresh, unpooled connection with `READINESS_DATABASE_TIMEOUT_SECONDS=2`
and one-second PostgreSQL statement/lock deadlines. These probe deadlines
do not limit ordinary learner/admin statements. Connection timeouts apply
per resolved address/host; sandbox readiness has its separate five-second
connection deadline. Server statement deadlines cannot bound every broken
network read, so gateway health probes must also have an external timeout.

Validate the placeholder Compose example without reading private env files:

```powershell
docker compose --env-file deploy/release.env.example -f docker-compose.release.yml config --no-env-resolution -q
```

That verifies Compose syntax only. It is not proof that production secrets,
DNS, HTTPS, provider consent, backups, recovery or external hosting are ready.
Never print resolved Compose configuration containing environment values.

Review and retain the full automated, browser, migration, sandbox and load
gate reports before release. External deployment, a backup restore drill and
live provider consent are operator actions; do not silently substitute unit
tests for them.

## Original-language question authoring — 23 October 2026

Administrators can save an English or Vietnamese original without a translation,
add a reviewed translation later, and preview before saving a draft. Menus and
question content have independent languages. The recorded session locale stays
fixed; the language selector displays reviewed snapshot translations when present,
with an original-language fallback. Stored grading evidence remains unchanged. See the [manual](learner-and-admin-manual.md) and [audit/traceability report](ux-simplification-audit-20261023.md).

Migration `012_question_original_locale.sql` adds the source language and permits
English display translations. It preserves existing English source defaults and
translation hashes, and does not update historical snapshots. Apply API and
frontend together only after the upgrade. For a persistent database, first obtain
explicit owner authorization and verify a restorable backup; this task applies
no migration to persistent development data. The normal migration command is
unchanged. PostgreSQL 17 Docker release verification remains required.

## Final integration acceptance follow-up - 23 October 2026

See [the final integration acceptance record](final-integration-acceptance-20261023.md) for subsequent PostgreSQL 17 migration/browser checks, the verified backup, and the remaining Docker gates. Earlier dated results above remain historical. Migration 012 is still not applied to persistent development data.
