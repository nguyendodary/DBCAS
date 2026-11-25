# Source code deliverable — DBCAS

This file is the entry point for the source-code part of the submission: how to
run the system, how the repository is organised, how to test it, and the gate
results that were actually observed. Every number below was re-measured on
2026-11-25; the command that produced it is named.

## 1. Requirements

| Requirement | Version used | Notes |
|---|---|---|
| Docker Desktop / Docker Engine | 29.8.1 | Linux containers; Compose v2 |
| WSL2 with a distribution | Ubuntu 24.04 | Needed only for writable (DML/DDL) SQL execution on Windows |
| Node.js | 24.x | Matches the CI runner |
| Python | 3.13 (container) / 3.14 (local venv) | The backend image is `python:3.13-slim` |
| Free ports | 18000 API, 18080 web, 18025 Mailpit UI, 11025 SMTP | Override with `LOCAL_*_PORT` |

No provider key is required to start: without `LLM_API_KEY` the AI features
report themselves as not configured and the practice flow uses the validated
bank.

## 2. Run it

```bash
git clone <repository> DBCAS
cd DBCAS
cp .env.example .env          # never commit .env
npm ci
npm start
```

`npm start` builds the images, applies `db/schema.sql` and the 28 migrations,
seeds the demo data (about three minutes on a cold volume), and prints
`DBCAS: http://localhost:18080`. Check readiness:

```bash
curl -s http://localhost:18080/readiness
# {"status":"ready","database":true,"sandbox":true,...}
```

Demo accounts (development only): `admin@dbcas.local` and
`learner@dbcas.local`, both with the password documented in the runbook. Do not
reuse them outside a local machine.

Stop and reset:

```bash
npm run stop      # stop the stack, keep the volume
npm run reset     # stop and delete the volume, then seed again
```

If `npm start` reports `Không đọc được group Docker socket`, set
`LOCAL_DOCKER_GID` in `.env` from
`wsl -e docker run --rm --network none --entrypoint stat -v /var/run/docker.sock:/var/run/docker.sock postgres:17 -c "%g" /var/run/docker.sock`
and start again.

## 3. Repository structure

```text
backend/                 FastAPI application
  app/routers/           8 router modules, 106 paths / 118 operations
  app/services/          73 service modules (use cases, transactions)
  app/repositories.py    13 repository classes (queries, locks)
  app/models.py          SQLAlchemy models, 67 tables
  tests/                 94 pytest modules + tests/dn/ (24 contract modules)
frontend/                React 19 + Vite single-page application
  src/                   pages, components, hooks, i18n, 54 vitest files
  e2e/                   25 Playwright specs, sharded by configuration
db/                      schema.sql, 28 forward migrations, seed packs
scripts/                 gates, generators, document build and verification
docs/                    architecture, diagrams, deliverables, submission
sandbox/                 ephemeral executor image and entrypoint
deploy/                  deployment assets
```

## 4. Test and gate commands

| Purpose | Command |
|---|---|
| Backend correctness | `python backend/manage.py lint` (ruff) |
| Backend tests | `python backend/manage.py test` |
| Frontend lint / format | `npm --prefix frontend run lint` / `run format:check` |
| Frontend unit tests | `npm --prefix frontend test -- --maxWorkers=2` |
| Browser end-to-end | `npm --prefix frontend run test:e2e` |
| Smoke | `npm run test:smoke` |
| QA browser sweep | `npm run test:qa` |
| API contract | `python scripts/export_openapi.py --check` |
| Route inventory | `npm run inventory:check` |
| Secrets | `npm run secrets:scan` |
| Diagrams and documents | `npm run docs:check` |
| Submission documents | `npm run docs:verify-word` |

## 5. Gate results observed on 2026-11-25

| Gate | Result | Evidence |
|---|---|---|
| Backend lint (ruff) | PASS, exit 0 | `manage.py lint` |
| Backend tests | **1 940 passed, 7 skipped**, exit 0 (24 min 22 s) | `pytest -q` log in the session record |
| Frontend unit tests | 54 files / **463 tests**, exit 0 | `vitest run` |
| Frontend lint and format | PASS, exit 0 | CI job `frontend-static` |
| Browser suites | 11 localization + 72 end-to-end + 12 practice + 3 smoke + 54 QA = **152 passed, 4 skipped** | sharded runs in the freeze logs |
| API contract | 106 paths / 118 operations, check PASS | `export_openapi.py --check` |
| Route inventory | PASS | `npm run inventory:check` |
| Secret scan (tree) | **Whole tree, 0 findings** (3,129 files at the last run) | `npm run secrets:scan` |
| Submission documents | 5 documents, **149 assertions, 0 failures** | `npm run docs:verify-word` |
| Documentation gate | PASS, 48 assertions, 67 tables / 561 columns / 122 FKs / 159 indexes / 28 migrations | `npm run docs:check` |
| Exact-commit CI | **12 of 12 jobs successful** | workflow run `45597486074` |

The CI workflow has six jobs; three of them expand into nine browser shards and
a fan-in job requires exactly nine success reports, which is why a run reports
twelve jobs.

## 6. Hygiene

- `.env` is ignored and untracked; only `.env.example` is in Git.
- `git ls-files` contains no `.env`, dump, screenshot with credentials or local
  artefact.
- The secret scanner covers seven patterns over the tree, staged blobs and
  archives up to 128 MiB; the six allowlist entries are hash-pinned fixtures.
- Generated PNGs under `docs/diagrams/schema-028/` are not committed; the
  document build uses the four ERD sheets and the diagram assets that are.

## 7. Where the other deliverables are

| Deliverable | Path |
|---|---|
| Five Word documents and rendered PDFs | `docs/submission/final/` |
| Document verification report | `docs/submission/final/verification/verification-report.md` |
| Traceability matrix | `docs/submission/final/TRACEABILITY.md` |
| Architecture freeze record | `docs/ARCHITECTURE_FREEZE.md` |
| Demo runbook | `docs/submission-pack/DEMO_CHECKLIST.md` |
| Handover summary | `docs/submission-pack/SUMMARY.md` |
