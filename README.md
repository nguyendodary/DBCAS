# DBCAS

**AI-Assisted Database Competency Assessment and Skill Gap Analysis** — C1SE.70, International School, Duy Tan University.

DBCAS is a web platform that evaluates a learner's PostgreSQL competency through adaptive assessments (MCQ, SQL coding, essay), then reports per-concept competency scores and skill gaps. Learner SQL runs in an isolated, read-only database sandbox; an external LLM provider (any vendor — provider-agnostic) assists with essay grading, concept tagging, and gap explanations.

This repository contains **code only** — project documents (Proposal, Database Design, User Stories) are kept outside the repo. When something is unclear, read those documents; do not guess.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 19 + Vite + Tailwind CSS 4 + Chart.js |
| Backend | FastAPI (Python 3.13) |
| System database | PostgreSQL 17 — accounts, assessments, attempts, competency evidence |
| SQL sandbox | A separate PostgreSQL 17 container that runs untrusted learner SQL (read-only, 3 s timeout, 256 MB, rollback) |
| AI | External LLM provider API — provider-agnostic (structured JSON outputs) |

## Layout

```
backend/    FastAPI app (API prefix /api/v1)
frontend/   React + Vite app
sandbox/    Dockerfile + init SQL for the isolated learner-SQL sandbox
db/         schema.sql — DDL for the system database, seed.sql — dev seed
docs/       api-conventions.md — API/error/auth conventions
```

Frontend files use English names matching their purpose: `Assessments_User`
lists assessments, `AssessmentAttempt_User` is the exam workspace,
`AssessmentReview_User` shows answers and explanations, and
`CumulativeCompetency_User` shows accumulated competency. The `frontend/src/pages/`
directory has three groups: `public/` for the landing and authentication pages,
`admin/` for administration (including `Dashboard_Admin.jsx`), and `user/`
for learner pages. `user/Settings_User.jsx` is shared by signed-in learners
and administrators through the existing `/settings` route.
Shared UI lives in `components/`, including `CompetencyPieChart` and
`CohortCompetencyBarChart`. Background assets use descriptive names such as
`learner-background.jpg` and `landing-background.mp4`.

## Quickstart

### Windows (PowerShell)

The repository includes `.env.example`, a runnable local development template.
Your private `.env` contains database passwords and login secrets and stays out
of Git. From the repository root, create it without overwriting existing settings:

```powershell
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
docker compose up -d
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.migrate
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open a second terminal at the repository root:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Open http://localhost:5173. The default template creates a local database;
it does not connect to the team's existing Neon accounts and results. To share
those records, ask the project owner privately for the Neon connection string
and set `DATABASE_URL` in your own `.env`, then restart the backend. Keep the
sandbox settings pointing at the local sandbox container. OAuth and AI features
require their own optional credentials in `.env`.

### Linux / macOS

```bash
if [ ! -f .env ]; then cp .env.example .env; fi  # keep existing configuration
docker compose up -d        # system db + sandbox; schema.sql + seed.sql auto-apply

cd backend
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m app.migrate   # additive upgrade, including existing volumes
.venv/bin/python -m uvicorn app.main:app --reload   # http://localhost:8000/docs
```

In a second terminal, from the repository root:

```bash
cd frontend && npm ci && npm run dev   # http://localhost:5173
```

On Windows use `py -3.13` to create the environment and
`.venv/Scripts/python.exe` for the commands; see the setup guide.

Seed creates a dev-only administrator `admin@dbcas.local` / `Admin123!`
(change before any real deployment). If host port 5432 or 5433 is taken,
set `POSTGRES_PORT`/`SANDBOX_PORT` in `.env`.

## Tests

```bash
cd backend && pytest        # spins a disposable postgres:17 container; needs Docker
```

## Backend layout

```
app/routers/    HTTP endpoints (controllers — no business logic)
app/services/   use-case rules: auth_service, grading_service, sql_service,
                sandbox_runner (isolated Docker PostgreSQL execution),
                llm/ (provider-agnostic REST client + llm_cache + PII redaction)
app/repositories.py   SQLAlchemy access
app/models.py   ORM access types; schema.sql + migrations are DDL authority
app/schemas.py  request/response DTOs
app/deps.py     JWT guard + require_roles(Learner|Administrator)
```

## Branching

- `main` — stable baseline; only merged from `develop` via PR.
- `develop` — integration branch; work branches merge here first.
- `frontend` — frontend team branch.
- Create a branch per task from `develop` (or `frontend` for UI work): `feat/<short-name>`, `fix/<short-name>`.
- Commit messages follow Conventional Commits — see `CONTRIBUTING.md`.

## Rules for contributors

- Use exact table/column/enum names from the Database Design — do not invent new ones.
- Never send learner personal data to external LLM APIs.
- Learner SQL runs only in the sandbox — never on the system database.
- No secrets in the repo — use `.env`.

## Operational and user guides

### Shared Admin content in Git

`db/shared_content.sql` contains the shared concepts, CLOs, prerequisite links,
question bank, answer keys, SQL tables and essay rubrics. It does **not** contain
accounts, passwords, OAuth information, learner sessions, answers or grades.
Question ownership on a new installation is assigned to an existing local
administrator; the original administrator's account is not copied.

In development, successful Admin content changes automatically update this file
after the database save. Restart the backend after updating the code to enable
this behavior. Commit `db/shared_content.sql` together with the code before
pushing. Saving on the website does not run Git commit or Git push.

For a new clone with a **new, empty database**, development Docker Compose loads
`schema.sql`, `seed.sql`, then `shared_content.sql`. Existing database volumes are
preserved and are not overwritten or synchronized when pulling code. Do not
delete a volume containing learner data to load this file.

To refresh the snapshot manually, run from `backend`:

```powershell
.\.venv\Scripts\python.exe -m app.content_snapshot export
```

For a manually initialized database, after applying schema and development seed:

```powershell
.\.venv\Scripts\python.exe -m app.content_snapshot restore
```

Restore refuses to run if any curriculum/question content already exists. The
snapshot supports fresh installations; it is not a cross-database merge tool.
Normal User registration and assessment use do not update the shared file. This
automatic export is disabled in staging and production.

- [Setup, additive migrations, benchmark and OAuth](docs/setup-and-migrations.md)
- [Learner and administrator manual](docs/learner-and-admin-manual.md)
- [Staging/production configuration and readiness](docs/deployment-and-readiness.md)
- [Full automated, browser, sandbox, migration and load gates](docs/testing-and-release-gates.md)
- [Owner-approved SQL execution and knowledge scope](docs/requirements-decisions.md)
- [Supervisor requirements, personalized assessments and verified results](docs/supervisor-implementation.md)

Use `DEPLOYMENT_MODE=development` locally. Staging/production fails closed on
placeholder JWT/database credentials and the active public seed password.
`/health` is process liveness; `/readiness` verifies required schema and sandbox.
The release Compose file is a separate named stack with no development seed.
Do not combine Compose files or delete volumes to upgrade.

The formal assessment is 60 minutes, 10 MCQ / two SQL / one essay, at most
13 questions, with three basic opening MCQs. Import the reviewed benchmark
to obtain a sufficient valid bank; the historical development seed alone is
not the formal release assessment. Server drafts survive refresh/resume and
timeout submits saved answers once. Historical question/config evidence is
snapshotted. Guidance remains shortfall-descending; prerequisites explain
readiness without changing the formal ranking.
