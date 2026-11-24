# DBCAS final architecture decisions

As of: 2026-11-24. Frozen baseline: `develop2` architecture-freeze commit recorded in [`ARCHITECTURE_FREEZE.md`](../ARCHITECTURE_FREEZE.md). Prior baseline: `6421b5ad44a0eaaeb9be8d26068c8ca434ae5bb7`. Scope: synthetic-data demo; production **HOLD**. This file is the single decision record for the submission documents. It records what the code does, not what a future product might do. No new table, migration, route or default-on flag is introduced by this record.

## Summary

| ID | Decision | Status |
| --- | --- | --- |
| F01 | FastAPI / SQLAlchemy / psycopg / PostgreSQL 17 backend; React 19 + Vite frontend | ADOPTED |
| F02 | Modular monolith with router -> service -> repository -> SQLAlchemy layering | ADOPTED |
| F03 | Relational schema with additive migrations and immutable result versions | ADOPTED |
| F04 | Deterministic AI #1 prompt template; validated AI #2 JSON; rule fallback | ADOPTED |
| F05 | OpenRouter release privacy: `deny` data collection, ZDR on, pinned endpoint | ADOPTED |
| F06 | Ephemeral Docker SQL executor; `shared` remains a development fallback | ADOPTED-DEMO-ONLY |
| F07 | Writable SQL only through the demo profile, guarded by `SANDBOX_MODE=ephemeral` | ADOPTED-DEMO-ONLY |
| F08 | Two grading paths: AI-official FIXED TEST and human-verified LEGACY | ADOPTED |
| F09 | JWT access + rotating refresh sessions; link-based password reset | ADOPTED |
| F10 | All capability flags default off; demo enables only explicit profiles | ADOPTED |
| F11 | One CI workflow, docs-only fast path, nine browser shards, three required checks | ADOPTED |
| F12 | Local Compose demo profile; no production deployment | ADOPTED-DEMO-ONLY |
| F13 | Executor broker code merged behind `SANDBOX_BROKER=false`; cutover not wired | DEFERRED (code present, default off) |
| F14 | Seed snapshot (`npm run demo:snapshot`) | ADOPTED-DEMO-ONLY |
| F15 | OTP password recovery (PR #25) | DEFERRED |

## ADR entries

### F01 — Stack

**Decision.** Python 3.13 + FastAPI `0.141.1`, SQLAlchemy `2.0.54`, psycopg `3.3.6`, Pydantic `2.13.5`, PostgreSQL 17; React `19.3`, Vite `8.3`, Node 24. Evidence: `backend/requirements.txt:1-6`, `frontend/package.json:22-46`, `docker-compose.local.yml:13-14`, `.github/workflows/dn-backend.yml:75-76`. **Alternatives considered.** A Django monolith; a Node-only stack; microservices. **Why chosen.** The repository already implements this stack and its tests, migrations, Docker images and CI. Rewriting would add risk without changing the demo's capability. **Consequences.** Two runtimes and a Python virtual environment are required; the browser and backend gates are separate. **Status.** ADOPTED.

### F02 — Layering

**Decision.** A modular monolith. HTTP routers under `backend/app/routers/` delegate to services under `backend/app/services/`, which use repositories in `backend/app/repositories.py` and SQLAlchemy models in `backend/app/models.py`; `backend/app/main.py:69-75` mounts seven routers. The worker and maintenance loop are in `backend/app/worker.py`, started from `main.py:25-43`. **Alternatives considered.** Microservices; a separate grading service; direct SQL in routers. **Why chosen.** One deployable unit matches one PostgreSQL database and the single-team demo; transaction boundaries and row locks stay in one process. **Consequences.** Services are imported directly; there is no network boundary. The broker is the only planned split (F13). **Status.** ADOPTED.

### F03 — Database design and versioning

**Decision.** `db/schema.sql` is the fresh-install DDL; `db/migrations/001..028` are additive upgrades with checksums and advisory locking. The generated catalogue reports **67 tables, 561 columns, 122 foreign keys, 159 indexes** and 28 migrations (`docs/diagrams/schema-028/schema-introspection.json`; `scripts/check_docs.py` prints the same totals). V1/V2 results are immutable: `session_result_version`, `session_result_version_score`, `session_result_criterion_score`, `session_result_publication` and `session_result_analysis` (`db/schema.sql:1207-1320`). `assessment_session` points at the current version through `current_result_version_id` (`db/schema.sql:1451-1478`). Migration 019 closes prebuilt assessments without deleting history (`db/migrations/019_archive_prebuilt_exams.sql:1-2`). **Alternatives considered.** ORM `create_all`; destructive migrations; mutable result rows. **Why chosen.** Checksummed upgrades preserve demo history; immutable versions make regrade auditable; PostgreSQL constraints enforce totals and completeness. **Consequences.** Every schema change needs a migration; the base DDL must be kept in sync manually, and `docs:check` compares both. **Status.** ADOPTED.

### F04 — AI pipeline AI1 -> AI2

**Decision.** AI #1 is a deterministic, versioned prompt builder; it does not score. AI #2 is an OpenAI-compatible chat-completions evaluator that returns validated JSON. If no key, timeout, malformed JSON or provider error occurs, the rule/template evaluator produces a clearly marked fallback. Evidence: `docs/ai-pipeline.md:1-29`, `backend/app/services/ai_stage_service.py:49-397`, `backend/app/services/evaluation_pipeline.py:159-162`. **Alternatives considered.** A single model that both builds and grades; a local self-hosted prompt model; free-form AI text. **Why chosen.** Separating prompt construction from evaluation makes the prompt hash stable and keeps MCQ/SQL scores deterministic. The local-model study was not adopted (`docs/ai-pipeline.md:31-40`). **Consequences.** AI quality depends on the external provider; the fallback is less specific and is labelled in the UI. No key is required for the demo. **Status.** ADOPTED.

### F05 — OpenRouter privacy settings

**Decision.** Defaults are `OPENROUTER_DATA_COLLECTION=deny` and `OPENROUTER_ZDR=true` (`backend/app/config.py:157-158`). In staging/production the application *requires* those values, an HTTPS official base URL, a concrete model, and the approved `deepinfra/turbo` endpoint (`backend/app/config.py:216-228`). No account-level setting is claimed; the account policy remains an owner action. **Alternatives considered.** Allow provider logging; any OpenRouter endpoint. **Why chosen.** Minimises student-data exposure and pins the reviewed route. **Consequences.** Other endpoints fail release validation; demo use without a key uses the deterministic fallback. **Status.** ADOPTED.

### F06 — Sandbox execution model

**Decision.** Demo and DN Compose run `SANDBOX_MODE=ephemeral` (`docker-compose.local.yml:38`, `docker-compose.dn.yml:50`). Each dataset gets a disposable PostgreSQL container created with `--network none`, read-only rootfs, UID/GID 10001, dropped capabilities, `no-new-privileges`, 256 MB, 1 CPU, 128 PIDs, a 45 s lifetime and tmpfs data (`backend/app/services/ephemeral_sandbox.py:93-130`). Learner SQL uses `learner_ro`; dataset setup uses a separate admin connection. The `shared` runner remains the config default for compatibility (`backend/app/config.py:60`), so any stack that does not set ephemeral uses it. **Alternatives considered.** Shared sandbox only; host PostgreSQL; a broker. **Why chosen.** Ephemeral containers contain writes and crashes and need no long-lived writable role. Shared mode is retained for legacy fixtures. **Consequences.** The API needs the Docker CLI/socket (known limitation F13); two executor slots are process-local; startup pays image/container latency. **Status.** ADOPTED-DEMO-ONLY.

### F07 — Writable demo mode

**Decision.** Writable SQL is opt-in only: `DBCAS_DEMO_PROFILE=writable` adds `docker-compose.demo-writable.yml`, setting `SANDBOX_MODE=ephemeral`, `SANDBOX_WRITABLE=true` and `SANDBOX_MULTI_STATEMENT=true` for that run (`docker-compose.demo-writable.yml:4-9`, `scripts/local.mjs:104-112`). `config.py:243-246` refuses writable mode unless the mode is ephemeral. The executor runs the script in a rolled-back transaction and drops the container (`ephemeral_sandbox.py:204-224`; `sandbox_runner.py:501-601`). Defaults stay false (`config.py:68-70`). **Alternatives considered.** Always-on DDL/DML; a shared writable role. **Why chosen.** The demo can show `CREATE/INSERT/SELECT` without weakening the default read-only path. **Consequences.** Writable mode is not production-approved; state grading is not implemented (`GRADING_STATE_MODE` is declared but unused). **Status.** ADOPTED-DEMO-ONLY.

### F08 — Grading modes

**Decision.** MCQ is deterministic. SQL is executed and compared on typed results (`docs/grading-and-sandbox.md:34-40`). Essay grading uses AI #2 or the fallback. Two publication paths exist: (a) **AI-official** FIXED TEST sessions: `review_policy=AI_OFFICIAL_REVIEW`, `result_version.ensure_official_v1` writes V1 and the session is published at finalize (`backend/app/services/assessment_lifecycle.py:233-238`, `backend/app/services/result_version.py:35-55,180-278`); (b) **Human-verified** LEGACY sessions: an administrator reviews SQL/essay and publishes (`backend/app/services/grading_review.py:59-86`). The API default is `HUMAN_VERIFIED` (`backend/app/schemas.py:240`), while the DB column default remains `IMMEDIATE` for historical rows (`db/schema.sql:676-680`). Regrade creates V2; V1 stays official while V2 is pending or failed (`docs/agent/DECISIONS.md:11-15`; `backend/app/services/review_regrade.py:1-8`). **Alternatives considered.** One universal manual path; AI always official. **Why chosen.** The FIXED paper is the assessment-shaped demo with anti-cheat; legacy practice keeps instructor control and audit. **Consequences.** The UI/copy must state which path a session uses; older docs that say "every result is human-approved" are inaccurate for FIXED sessions. **Status.** ADOPTED.

### F09 — Authentication and reset link

**Decision.** Short-lived HS256 access JWT (60 min default, absolute session cap 480 min) plus random refresh tokens stored as SHA-256 hashes, rotated once, with family revocation on replay (`backend/app/config.py:25-29`; `backend/app/services/refresh_tokens.py`; `db/migrations/016_refresh_sessions.sql`). Roles are `Learner` and `Administrator`; the UI label is **User** (`docs/architecture.md:9`). Self-service recovery is a single-use **link** (`/reset-password?token=...`), stored hashed with a 15-minute TTL (`backend/app/routers/auth.py:97-172`); SMTP is optional and uses Mailpit in development. Google/GitHub OAuth is optional and disabled by empty client IDs (`backend/app/config.py:104-122`). **Alternatives considered.** OTP codes (#25); long-lived JWTs; server sessions. **Why chosen.** Link recovery is implemented, test-covered, and reversible; rotating refresh tokens limit replay. **Consequences.** OTP is not adopted; a real SMTP relay is required outside development; OAuth buttons show a configuration notice when disabled. **Status.** ADOPTED.

### F10 — Flags and defaults

**Decision.** Capability flags default off: `SANDBOX_MULTI_STATEMENT=false`, `SANDBOX_WRITABLE=false`, `GRADING_STATE_MODE=false`, `SANDBOX_BROKER=false`, `AUTO_GRADE_ESSAYS=false`, `QUESTION_TRANSLATION_ENABLED=false`. `VITE_DEMO_FREE_PRO=true` is the demo UI default (localStorage plan starts on Free) and has no backend effect. (`config.py:68-70,81,167-169`; `.env.example`). The only default-on AI behavior is the deterministic fallback, which requires no provider. Local Compose explicitly sets `AUTO_GRADE_ESSAYS=true` for the demo worker (`docker-compose.local.yml:47`). **Alternatives considered.** Enable capabilities by default; one mega-flag. **Why chosen.** An unchanged deployment keeps the legacy read-only, human-verified behaviour; demo profiles are explicit. **Consequences.** The demo needs `DBCAS_DEMO_PROFILE` for writable/Free-Pro; forgetting it yields the safe path. **Status.** ADOPTED.

### F11 — CI strategy

**Decision.** One workflow, `.github/workflows/dn-backend.yml`, runs on PR/push to `develop2` and `main`. Required checks are `secrets`, `backend` and `frontend-local` (`dn-backend.yml:2-3`). A docs-only change set skips the heavy jobs (`:15-46`). The browser matrix has nine legs: three E2E, three QA and three smoke (`:166-267`), plus `frontend-static`. Exact-head evidence is mandatory; a red run is classified, not blindly retried. **Alternatives considered.** Per-module workflows; nightly only; no sharding. **Why chosen.** Sharding keeps a full-stack run near 20 minutes; the aggregator prevents a green required check when a shard is red. **Consequences.** Nine Compose stacks consume significant machine time; the docs-only path means a docs PR cannot prove runtime behavior. **Status.** ADOPTED.

### F12 — Deployment and demo profile

**Decision.** The supported path is local Docker Compose. `npm start` uses `docker-compose.local.yml` with web `18080`, API `18000`, Mailpit `18025` (`README.md:27-35`; `docker-compose.local.yml:79-114`). `docker-compose.release.yml` exists as a release-shaped stack but is not deployed; production is **HOLD**. **Alternatives considered.** Cloud deployment; Kubernetes; bare metal. **Why chosen.** The submission is a synthetic-data demo, not a production service. Local Compose is reproducible and test-covered in CI. **Consequences.** Ports, Docker, and synthetic seed data define the demo; production substrate, TLS, secrets and monitoring remain owner actions. **Status.** ADOPTED-DEMO-ONLY.

## Explicit verdicts

| Item | Verdict | Basis |
| --- | --- | --- |
| Executor broker cutover | **Not in scope; future work.** | Code merged as `23d4d65` with B2 constrained runtime; `SANDBOX_BROKER=false` (`config.py:81`) and `sandbox_runner` still uses Docker CLI/socket. See `docs/analysis/broker-validation.md`. |
| `docker.sock` in the API | **Known limitation.** | `docker-compose.local.yml:72,84-85` mounts it for init/app; the API shells out to Docker (`ephemeral_sandbox.py:25-67`). Closing #66 needs the broker (F13). |
| Free/Pro | **UI-only simulation.** | `frontend/src/demo/freePro.jsx` stores the plan in `dbcas_demo_plan`; `VITE_DEMO_FREE_PRO=true` is the demo default; no backend route, table or payment. Free locks Mode 2 and shows `5 sessions/day`; Pro unlocks Mode 2. |
| Seed snapshot | **Adopted demo-only.** | `npm run demo:snapshot` in `package.json`; `scripts/demo-seed-snapshot.mjs` writes a versioned data-only dump; `seed_demo.py:_restore_snapshot` restores it with full-seed fallback. |
| OTP #25 | **Not adopted.** | The implemented flow is a reset link (`auth.py:97-172`); #25 remains an unmerged owner item. |
| Production | **HOLD.** | No release deployment is claimed; `docs/agent/STATUS.md:7` and `docs/demo/README.md:3-5`. |

## Consequences for the submission

- The documents use the generated counts above, the actual route inventory
(106 paths / 118 operations) and the actual frontend routes (24 entries).
- FIXED TEST and LEGACY sessions are described separately; no document says all
results require human approval.
- Writable SQL, Free/Pro, broker, snapshot and OTP are labelled demo-only or
future work, never as delivered production features.
- The only supported deployment claim is the local demo profile in F12.
