# Setup, upgrades and local provider configuration

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
startup rejects an active account retaining it. Self-registration creates
Learners; authenticated provisioning creates disabled Administrators only.

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
rubric data. Existing attempt snapshots remain untouched. The recovered essay
uses its historical three-band rubric; the current grader's four-band
validation rejects that rubric, so it needs owner review before a fresh
database can validate or grade that question.

The Vietnamese content source is `db/question_translations_vi.json`; each
question pack points to it with `translations_manifest`, keyed by the pack's
stable question key. It contains display prose only. The checked-in packs
contain 23 benchmark questions, three DML/DDL questions and 415 PostgreSQL
questions: 441 total (326 MCQ, 67 SQL and 48 Essay). Run
`py -3.13 db/validate_question_localization.py` to check coverage and protected
tokens. Use both supplement flags to import the extended bank.

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
