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

## Quickstart

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

This project has no hosted automation: every gate is run locally and its
result is recorded by the reviewer. The complete procedure is in
[testing and release gates](docs/testing-and-release-gates.md).

```bash
cd backend && pytest        # spins a disposable postgres:17 container; needs Docker
```

```bash
cd frontend && npm ci && npm test && npm run build   # unit/component tests + production build
cd frontend && npm run test:e2e                      # Playwright browser journeys (Chromium)
```

Browser journeys for Firefox and WebKit are run with `DBCAS_BROWSER=firefox`
and `DBCAS_BROWSER=webkit` before `npm run test:e2e`. Load, release-image and
sandbox gates stay explicit local commands; see the gates document.

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

- [Setup, additive migrations, benchmark and OAuth](docs/setup-and-migrations.md)
- [Learner and administrator manual](docs/learner-and-admin-manual.md)
- [Staging/production configuration and readiness](docs/deployment-and-readiness.md)
- [Local testing, browser, sandbox, migration and load gates](docs/testing-and-release-gates.md)
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
