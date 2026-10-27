# DBCAS

Current development state: [24 October activation](docs/development-activation-20261024.md).
Migration 012 is applied to persistent development; the running application uses
that original database. Older dated recovery reports retain their historical state.

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

## Original-language question authoring — 23 October 2026

Administrators can save an English or Vietnamese original without a translation,
add a reviewed translation later, and preview before saving a draft. Menus and
question content have independent languages. The recorded session locale stays
fixed; the language selector displays reviewed snapshot translations when present,
with an original-language fallback. Stored grading evidence remains unchanged. See the [manual](docs/learner-and-admin-manual.md) and [audit/traceability report](docs/ux-simplification-audit-20261023.md).

Migration `012_question_original_locale.sql` adds the source language and permits
English display translations. It preserves existing English source defaults and
translation hashes, and does not update historical snapshots. Apply API and
frontend together only after the upgrade. For a persistent database, first obtain
explicit owner authorization and verify a restorable backup; this task applies
no migration to persistent development data. The normal migration command is
unchanged. PostgreSQL 17 Docker release verification remains required.


## 23 October 2026 follow-up

[Architecture diagram inventory and faithful semantic comparisons](docs/diagrams/README.md). Earlier dated observations and test results remain historical;
the follow-up records subsequent changes and unresolved gates.

Latest: [final integration acceptance](docs/final-integration-acceptance-20261023.md),
[academic amendments](docs/academic-reconciliation-20261023.md), and
[diagram acceptance review](docs/diagrams/acceptance-review-20261023.md).
These distinguish disposable PostgreSQL 17 checks and a verified backup from
the still-incomplete Docker release gates. Persistent migration 012 remains
pending owner authorization. *(Superseded on 25 October: the owner-authorized
activation applied `012`, `013` and `014` to the persistent development database;
see [activation-release-20261025.md](docs/activation-release-20261025.md) and the
[27 October migration state check](docs/setup-and-migrations.md).)*

Current continuation: [Docker and integration remediation](docs/docker-stabilization-acceptance-20261023.md),
[local test troubleshooting](docs/local-integration-troubleshooting.md), and
[optional translation drafts](docs/draft-question-translation.md). Draft preparation
is disabled by default and never approves machine output automatically.

Latest infrastructure investigation: [Docker/WSL root-cause recovery](docs/docker-wsl-root-cause-recovery-20261023.md).
It records the failed finite stability window, independently inspected Chromium
failures, protected data fingerprints and the owner-approval recovery boundary.

## 27 October 2026 - documentation/codebase alignment and diagrams as code

The full audit, the document-by-document mismatch matrix and the diagram preservation
record are in [documentation-alignment-20261027.md](docs/documentation-alignment-20261027.md).
Proposed academic wording and the decisions still reserved to the document owner are in
[academic-reconciliation-20261027.md](docs/academic-reconciliation-20261027.md). No original
university Word/PDF document was opened for writing, and no existing diagram was replaced.

Every repository diagram is now text-first and reproducible from one command:

| Command | What it does |
| --- | --- |
| `npm ci` | installs the pinned toolchain: `@mermaid-js/mermaid-cli` 12.0.0 and `@viz-js/viz` 3.31.0 |
| `npm run diagrams:check` | discovers every source, validates it, re-renders into a scratch directory and exits non-zero on any drift |
| `npm run diagrams:render` | writes the committed SVGs and `docs/diagrams/rendered/manifest.json` |
| `npm run diagrams:setup` | reports pinned versions and prerequisites; fetches the pinned PlantUML jar on demand into gitignored `tools/` after SHA-256 verification |

Changing a diagram means editing a `.dot` file, a ````mermaid```` fence or a `.puml`
source and re-running `npm run diagrams:render` - never redrawing a picture. The physical
ERD is generated from the real PostgreSQL 17 catalog:
`backend/.venv/Scripts/python.exe scripts/generate_schema_catalog.py "<dsn>" --load --write`
against a disposable database, and `scripts/validate_diagrams.py` now also proves the
committed ERD still matches that generated catalog. `node scripts/render_diagrams.mjs`
keeps working and simply delegates to the same implementation.

Rendering drives an already installed Chrome/Edge binary; it downloads no browser and
never passes a flag that weakens the Chromium sandbox. The toolchain stays outside the
application: no backend or frontend dependency, no CI workflow, no network service.
