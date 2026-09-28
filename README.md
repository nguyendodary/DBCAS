# DBCAS

AI-Assisted Database Competency Assessment and Skill Gap Analysis — C1SE.70, International School, Duy Tan University.

This repository contains **code only**. Project documents (Proposal, Database Design, User Stories) and the binding specification (`README.md` in the proposal workspace) live outside this repo — do not commit documents here.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS + Chart.js |
| Backend | FastAPI (Python) |
| System DB | PostgreSQL 16 (`db` service) |
| SQL sandbox | Separate PostgreSQL 16 in Docker (`sandbox` service) — see ADR-001 |
| AI | OpenAI API (structured JSON outputs) |

## Layout

```
backend/    FastAPI app (API prefix /api/v1)
frontend/   React + Vite app
sandbox/    Dockerfile + init SQL for the isolated learner-SQL sandbox
db/         schema.sql — generated DDL for the system database
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

- `main` — stable baseline. Do not push work-in-progress here.
- Create a branch per task: `feat/<short-name>`, `fix/<short-name>`.
- Open a pull request to merge back into `main`.
- Commit messages follow Conventional Commits — see `CONTRIBUTING.md`.

## Rules for contributors (human or AI agent)

- Use exact table/column/enum names from the Database Design — do not invent new ones.
- Never send learner PII to external LLM APIs.
- Learner SQL runs only in the sandbox (read-only role, 3 s timeout, 256 MB cap, rollback).
- No secrets in the repo — use `.env`.
