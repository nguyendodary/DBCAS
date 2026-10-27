# Setup, upgrades and local provider configuration

Migration 008 adds concept keywords/objectives, assessment release policies,
immutable session start/policy context, grading reviews and publication events.
It preserves historical fully graded results and withholds incomplete grades.
Run the existing migration command before using the updated API. See the
[supervisor implementation and preservation policy](supervisor-implementation.md).

Migration 009 repairs legacy release states when stale numeric scores coexist
with unfinished grading. It preserves all answer/score evidence, records release
events and uses bounded locks; a busy database rolls the migration back safely
for retry. Keep applied migration 008 unchanged. Completed upgrades have no
destructive down migration; retain the schema and use a reviewed forward fix.

DBCAS targets Python 3.13, Node 24, PostgreSQL 17 and Docker Compose. Use a
virtual environment. The release backend image pins the documented Python
minor version; a different host interpreter must be reported in verification.

## Windows development setup

Run from the repository root. Create `.env` from `.env.example` only if it
does not already exist. Keep existing credentials and port choices.

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up -d db sandbox
docker compose ps
```

Set `DATABASE_URL`, `SANDBOX_URL` and `SANDBOX_ADMIN_URL` to match the chosen
host ports. Database and sandbox are different PostgreSQL servers. The SQL
learner role is `learner_ro`; the privileged sandbox connection only creates
and cleans execution schemas. Never point either sandbox URL at the app DB.

```powershell
cd backend
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m app.migrate
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

UI: `http://localhost:5173`; API: `http://localhost:8000/api/v1`.
`/health` checks the process. `/readiness` checks required app schema and the
read-only sandbox connection. Wait for database startup before migrating.
On POSIX, use `python3.13 -m venv .venv` and `.venv/bin/python` instead.

The development seed administrator is `admin@dbcas.local` / `Admin123!`.
That public password is for local development only. Staging/production
startup rejects an active account retaining it. Self-registration always
creates Learners. Administrator provisioning and role assignment require a
separately provisioned role manager.

## Existing-volume upgrades

`schema.sql` is the fresh-install DDL. Docker's init scripts do **not** rerun
for an existing volume. Run `python -m app.migrate` with the application's
configured database connection before serving the updated API. It applies
ordered SQL files under `db/migrations`, under an advisory lock, transaction,
and checksum ledger. Repeating the command is safe. Never edit an applied
migration: add the next numbered migration instead.

The upgrade adds OAuth identities, prerequisites, durable drafts, grading
jobs, immutable evidence/config snapshots, shared authentication state,
question/assessment versions, canonical statuses, and deployment roles.
It neither resets tables nor removes learners/attempts. Take the operator's
usual backup before a deployment upgrade; never delete a volume to upgrade.

Migration 011 adds the default-deny `account.can_manage_roles` capability and
append-only `account_role_audit` records. Existing accounts are preserved and
are not automatically authorized. The first trusted Administrator created
with `python -m app.bootstrap_admin` is also the initial role manager. For an
existing installation, an operator with trusted database access explicitly
selects an active Administrator by account ID and runs:

```powershell
cd backend
.venv/Scripts/python.exe -m app.bootstrap_role_manager --account-id <ACCOUNT_ID>
```

The command prompts for the selected account's email without echoing it. It
refuses a missing/inactive/non-Administrator account or an existing active
role manager. There is no HTTP bootstrap endpoint. Use the same process in
protected environments only through the approved database-operator workflow;
do not grant this capability to every Administrator or select an account by a
public development email alone. Role changes are serialized, audited, and
visible to authorization checks immediately because API requests load current
roles from the database rather than trusting JWT role claims.

Legacy evidence is backfilled from the context available at migration time
and marked as legacy. Values lost through edits before that cutoff cannot
be reconstructed. New and backfilled snapshots are immutable thereafter.
Legacy nonformal assessment configurations are preserved for historical
reports; create a new formal version for future sessions.

## Reviewed academic benchmark

The pack is `db/benchmark_pack.json`: 15 concepts (six SQL, six relational
design and three recovered legacy concepts), two CLOs, dependencies, 14 MCQs,
seven SQL tasks with regular/edge datasets, two essays, and a formal 60-minute
assessment. It contains no learner records. Import with an existing Administrator:

```powershell
cd backend
.venv/Scripts/python.exe -m app.benchmark --admin-email admin@dbcas.local --fill-missing-techniques
```

The flag explicitly permits adding reviewed SQL-technique metadata to
matching concepts whose field is empty. Existing nonempty metadata conflicts
are rejected. Existing CLO links, pending review decisions and prerequisite
edges survive. Reimport is repeatable; an existing identical prompt with
different content is a conflict, not permission to overwrite it. Resolve a
reported conflict through the admin UI before importing again. Import is
additive and uses ordinary management services; individual accepted records
may persist before a later conflict, so a retry must use the same pack.

To add the owner-approved DML/DDL knowledge topics, append
`--include-sql-knowledge` to that command. The supplement adds two concepts,
two MCQs, one four-level essay and a separately titled formal assessment;
existing core assessment targets remain unchanged. See `requirements-decisions.md`.

Four legacy core records were recovered read-only from validated database
questions 2–5 and added to the reproducible benchmark source without changing
their answer keys, SQL fixtures, points, difficulty, concept mappings or
rubric data in recovery commit `6233e7c`. Existing attempt snapshots remain
untouched. Pack 1.3 retains Essay ID 5 as retired legacy content and adds a
distinct four-band IDX Essay successor; see [the recovery record](core-question-recovery.md).
For the existing development database's applied retirement, preserved evidence,
and the originally detected PostgreSQL ID 119 import conflict, see
[the resolution verification](legacy-essay-resolution.md).
That conflict is now reconciled; the development bank has 442 current VI
translations. See [the reconciliation audit](pg-m089-assessment-2-reconciliation.md).

For an existing bank with the exact reviewed pre-correction `pg-m089` version,
run the read-only preflight before applying the guarded correction:

```powershell
cd backend
.venv/Scripts/python.exe -m app.reconcile_bank
.venv/Scripts/python.exe -m app.reconcile_bank --apply --admin-email admin@dbcas.local
```

This maintenance command requires all source questions to exist already. It
refuses owner content differences, ambiguous prompts, extra/missing questions,
and referenced historical versions of the old question. It preserves option
IDs, advances only the known current question version, and uses the normal
pack importer for translations. A repeated apply leaves matching content and
translation timestamps unchanged. Fresh databases still use `app.benchmark`.

`db/assessment_templates/postgres_foundations_current.json` is a forward-looking
60-minute/10MCQ/2SQL/1Essay template using existing current topic coverage. Map
its concept codes to IDs through the normal admin workflow when creating a
new draft. It is not automatically published and never updates assessment 2.

The Vietnamese content source is `db/question_translations_vi.json`; each
question pack points to it with `translations_manifest`, keyed by the pack's
stable question key. It contains display prose only. The checked-in packs
contain 24 benchmark questions, three DML/DDL questions and 415 PostgreSQL
questions: 442 stored (326 MCQ, 67 SQL and 49 Essay), of which 441 are active. Run
`py -3.13 db/validate_question_localization.py` to check coverage and protected
tokens. Use both supplement flags to import the extended bank.

## Durable start/resume request bindings

Migration `010_session_start_request_bindings.sql` adds the immutable
`session_start_request` table, indexed by session and keyed by authenticated
learner plus request UUID. A composite foreign key enforces session ownership.
Known original `start_request_id` values are backfilled; historical resume UUIDs
were never stored and cannot be reconstructed. Sessions, answers, scores and
snapshots are preserved. The additive DDL uses a five-second lock deadline and
is safely retryable through the existing checksum migration runner.

Run `.venv/Scripts/python.exe -m app.migrate` from `backend` before starting the
updated API. Readiness rejects a missing binding table. Every accepted resume
UUID now points to its existing session even after completion or timeout;
changing its assessment or selections returns a conflict. New UUIDs can still
create subsequent attempts after the previous attempt ends. Do not delete the
binding table during rollback: old application versions ignore it, but cannot
honor these additional retry bindings.

## Google and GitHub OAuth locally

Keep provider secrets in the backend `.env`. Never add `VITE_*` secrets.
Register separate provider applications for each deployment origin. For the
local Vite origin configure:

| Setting | Google | GitHub |
|---|---|---|
| Client ID / secret | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` |
| Callback variable | `GOOGLE_REDIRECT_URI` | `GITHUB_REDIRECT_URI` |
| Local callback | `http://localhost:5173/api/v1/auth/oauth/google/callback` | `http://localhost:5173/api/v1/auth/oauth/github/callback` |

Set `FRONTEND_URL=http://localhost:5173` and an explicit matching CORS origin.
Google's authorized JavaScript origin is the UI origin. GitHub's homepage
URL is the UI origin, with the exact callback above. Add intended test users
to a Google consent application in testing mode. Grant verified-email access
for GitHub. Restart the API after changing configuration.

`GET /api/v1/auth/oauth/providers` reports whether each provider is enabled.
Check both sign-in buttons in your own browser. Consent and credentials stay
between you and the provider. The backend handles code exchange, state,
Google PKCE, verified-email identity linking, and an atomic expiring one-time
handoff. Provider access tokens never reach the SPA. New social accounts are
Learners. A disabled account cannot gain access by social sign-in.

The browser must return through the same UI origin and its `/api` proxy:
the state/handoff cookies are HttpOnly. Avoid mixing `localhost` and
`127.0.0.1` during a live sign-in. Log only provider configured YES/NO and
the safe error code; never log auth codes, tokens, secrets or callback queries.

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

Later blocker-remediation evidence and the exact owner activation procedure are
in [Docker stabilization acceptance](docker-stabilization-acceptance-20261023.md).
Use that report for current gate results; the earlier record remains historical.
The optional translation draft feature is separately disabled by default and
does not change migration 012 or authorize persistent activation.

## Migrations 013 and 014 - current state, 27 October 2026

The two sentences above that reported migration 012 as not yet applied to
persistent development data are **historical**. The owner-authorized 25 October
activation described in [activation-release-20261025.md](activation-release-20261025.md)
applied the later migrations, and a read-only check of the persistent development
database on 27 October 2026 shows `schema_migration` holding all of `001` through
`014`, 35 relations in `public` (34 application tables plus the migration runner's
own `schema_migration` bookkeeping table) and 49 application foreign keys.

`db/schema.sql` stays the consolidated fresh-install schema: a new database created
from it needs no upgrade path for 001-014, and it is byte-reproducible through the
checksummed migration runner.

- `013_assessment_blueprints.sql` adds the immutable `assessment_blueprint` table
  (`approval_basis`/`approved_by`/`approved_at`, a `status` CHECK, an
  `assessment_blueprint_counts_check` that requires
  `target_mcq + target_sql + target_essay = max_questions`, a difficulty-band CHECK,
  a version uniqueness CHECK and `assessment_blueprint_version_unique` over
  `(assessment_id, subject_area, difficulty_band, version_no)`), a nullable
  `assessment_session.blueprint_id`, a CASCADE-owned `assessment_id` foreign key, a
  nullable `approved_by` reference to `account`, and the
  `assessment_blueprint_immutable` trigger, which blocks `UPDATE` while leaving
  deliberate deletion to controlled re-seeding. `backend/app/services/blueprints.py`
  resolves a session's blueprint (`resolve_blueprint`) and proves pool coverage
  (`verify_quotas`) before any question is served.
- `014_adaptive_events.sql` adds `adaptive_event`, keyed by
  `(session_id, round_no, event_type)` with `event_type IN ('batch','decision')`,
  a JSONB object CHECK and a `round_no BETWEEN 1 AND 13` bound, plus the
  `adaptive_event_immutable` trigger, which blocks both `UPDATE` and `DELETE`.
  `backend/app/services/batch_adaptive.py` writes the selection and decision trail
  through it; nothing is rewritten retrospectively.

Nothing in this section needs a new command: `.venv/Scripts/python.exe -m app.migrate`
from `backend` remains the way to bring a database forward, and readiness still
rejects a missing binding table.

The diagram evidence for this schema is generated, not hand-drawn. Against a
**disposable** PostgreSQL 17 loaded from `db/schema.sql` only, run
`backend/.venv/Scripts/python.exe scripts/generate_schema_catalog.py "<libpq dsn>" --load --write`
to refresh [schema-catalog.json](diagrams/schema-catalog.json), the
[foreign key ledger](diagrams/physical-schema-relationships.json) and
`physical-schema.dot`; then `npm run diagrams:render`. The generator refuses a
target that already holds rows, so it cannot rewrite persistent data. See
[the diagrams guide](diagrams/README.md).
