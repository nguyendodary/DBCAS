# DBCAS

**AI-Assisted Database Competency Assessment and Skill Gap Analysis** — C1SE.70, International School, Duy Tan University.

DBCAS is a web platform that evaluates a learner's PostgreSQL competency through adaptive assessments (MCQ, SQL coding, essay), then reports per-concept competency scores and skill gaps. Learner SQL runs in an isolated, read-only database sandbox; OpenAI assists with essay grading, concept tagging, and gap explanations.

This repository contains **code only** — project documents (Proposal, Database Design, User Stories) are kept outside the repo. When something is unclear, read those documents; do not guess.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS + Chart.js |
| Backend | FastAPI (Python) |
| System database | PostgreSQL 16 — accounts, assessments, attempts, competency evidence |
| SQL sandbox | A separate PostgreSQL 16 container that runs untrusted learner SQL (read-only, 3 s timeout, 256 MB, rollback) |
| AI | OpenAI API (structured JSON outputs) |

## Layout

```
backend/    FastAPI app (API prefix /api/v1)
frontend/   React + Vite app
sandbox/    Dockerfile + init SQL for the isolated learner-SQL sandbox
db/         schema.sql — DDL for the system database
```

## Quickstart

```bash
cp .env.example .env        # fill in values, never commit .env
docker compose up -d        # starts system db (5432) + sandbox (5433)

cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

cd frontend && npm install && npm run dev
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
