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
cp .env.example .env        # fill in values, never commit .env
docker compose up -d        # system db + sandbox; schema.sql + seed.sql auto-apply

cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000/docs

cd frontend && npm install && npm run dev   # http://localhost:5173
```

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
app/models.py   ORM mirror of schema.sql
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
