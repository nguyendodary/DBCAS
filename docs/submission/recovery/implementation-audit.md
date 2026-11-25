# Independent implementation audit (read-only)

**Repo root:** `C:\Users\kudot\Downloads\proposal test\DBCAS`
**Branch:** `develop2`, HEAD `66045b74b3e7fcd7f88afb590b8f58d750013c9a` (clean tree before this report; the only untracked path was `docs/submission/recovery/`).
**Method:** source/schema/config/test/log inspection only. No files were changed except this report. No suite was fully executed; counts come from static enumeration, committed artifacts and saved freeze logs. AGENTS.md and CONTRIBUTING.md were read first.

---

## 1. Architecture

### Backend (`backend/app/`)
- FastAPI app: `backend/app/main.py:46` (`FastAPI(title="DBCAS API", version="0.1.0", lifespan=lifespan)`).
- Lifespan: DB readiness validation, optional broker config validation, deployment-account guard, maintenance worker thread — `backend/app/main.py:25-43`.
- Middleware: CORS with configured origins (`main.py:59-65`), security headers on every response (`main.py:49-57`).
- Router modules **registered: 7** — `auth, oauth, admin, assessments, concepts, sessions, practice` at `backend/app/main.py:15` and `main.py:69-75`; files `backend/app/routers/{auth,oauth,admin,assessments,concepts,sessions,practice}.py` plus an **empty** `backend/app/routers/__init__.py`.
  - Counting convention note: there are **8 `.py` files** in `backend/app/routers/` (including `__init__.py`). The claim "8 router modules" in `docs/submission-pack/SOURCE_CODE.md:61` is true only under that convention; only 7 define routers.
- Service modules: **72 top-level `.py` files** in `backend/app/services/` excluding `__init__.py`; **73 including `__init__.py`** (the convention used by SOURCE_CODE.md:62). Two service subpackages exist: `backend/app/services/broker/` (6 modules: admission, client, errors, runtime, schemas, service) and `backend/app/services/llm/` (5 modules: errors, provider, sanitize, service, validation) — **83 actual service modules, 86 `.py` files recursively** including the two subpackage `__init__.py`.
- Repository layer: **13 classes** in `backend/app/repositories.py` (lines 63, 189, 219, 666, 743, 859, 1025, 1090, 1415, 1443, 1502, 1559, 1714): Account, Readiness, Assessment, ConceptGraph, Competency, Curriculum, Document, Question, LlmCache, Security, PasswordReset, Analytics, Statistics.
- ORM: `backend/app/models.py` — **67 `__tablename__` declarations**, matching the 67 documented schema tables.
- Configuration: `backend/app/config.py` (Pydantic `BaseSettings`, all settings including flags), errors: `backend/app/errors.py`, auth deps: `backend/app/deps.py`, JWT/bcrypt: `backend/app/security.py`, migrations runner: `backend/app/migrate.py`, OpenAPI post-processing: `backend/app/openapi.py`.

### Frontend (`frontend/src/`)
- React 19 + Vite SPA (`frontend/package.json:22-47`): `react ^19.3.0`, `react-dom ^19.3.0`, `react-router-dom ^7.18.4`, `vite ^8.3.1`, `vitest 4.1.12`, `@playwright/test 1.64.0`, `tailwindcss ^4.3.3`, `i18next 26.4.3`, `axios ^1.20.0`, `chart.js ^4.5.1`.
- Structure: `pages/` (16 top-level JSX files + `pages/admin/`), `components/` (26 JSX), `demo/freePro.jsx`, `i18n/`, `test/`, `assets/`, and hooks at the `src/` root (`useAnswerDraft.js`, `usePaperDraft.js`, `usePendingResults.js`, `useTabLeaveGuard.js`). Entry `frontend/src/main.jsx`, routes in `frontend/src/App.jsx` (24 route strings per `docs/diagrams/schema-028/manifest.json:693-718`), 6 admin nav items (`manifest.json:719-726`; verified in `frontend/src/components/Layout.jsx`).
- 54 vitest files under `frontend/src/` (82 test files when `scripts/*.test.mjs` are included).

### Deployment
- 9 Compose files: `docker-compose.yml`, `docker-compose.{local,dn,qa,real-qa,release,demo-snapshot,demo-writable,demo-free-pro}.yml`.
- 4 Dockerfiles: `backend/Dockerfile`, `frontend/Dockerfile`, `sandbox/Dockerfile` (`FROM postgres:17` + `sandbox/init/`), `sandbox/Dockerfile.ephemeral` (postgres 17 + Python runner, uid/gid 10001).
- `deploy/` contains `nginx.conf` and `release.env.example` only (release-shaped assets, not deployed).
- Local compose services: `mailpit, db, executor-image, init, app, frontend` (`docker-compose.local.yml`; confirmed in `manifest.json:566-573`). QA Compose adds `qa-ai` (`manifest.json:574-582`).
- No production deployment is performed; see §7.

---

## 2. Database — independent counts and method

**Method / exact commands used** (PowerShell, read-only, from repo root):
1. `Get-ChildItem db\migrations\*.sql` → **28** files (`001_account_identity.sql` … `028_review_deviation_confirmation.sql`).
2. `Select-String -Path db\schema.sql -Pattern "CREATE TABLE"` → **68 statements**. Regex extraction of table names (`CREATE TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(\w+)`) piped through `Sort-Object -Unique` → **67 distinct tables**. `concept_dependency` is created twice (`db/schema.sql:83` and `:440` with `IF NOT EXISTS`), which explains 68 statements vs 67 tables.
3. `Select-String -Path db\schema.sql -Pattern "CREATE TYPE"` → **0** matches: there are **no PostgreSQL enum types** (the introspected count is also 0). The task's "count enum types" result is zero.
4. Loaded committed introspection with `Get-Content docs\diagrams\schema-028\schema-introspection.json -Raw | ConvertFrom-Json`, then counted `.tables.Count`, `sum(.columns.Count)`, `.foreign_keys.Count`, `.indexes.Count`, `.enums.Count`. Result (PostgreSQL **17.12**): **67 tables / 561 columns / 122 foreign keys / 159 indexes / 0 enums**. `schema_migration` is **absent** from that table list.
5. `Select-String -Path backend\app\models.py -Pattern "__tablename__"` → **67** ORM tables.
6. Legacy/retired tables: `docs/diagrams/schema-028/manifest.json:518-523` lists exactly four — `assessment`, `assessment_blueprint`, `assessment_concept`, `assessment_question`. Enforced by `scripts/check_docs.py:156-164` (including an ERD `[legacy/retired]` marker check). `assessment_session` is **not** legacy: it carries `purpose`/`purpose_source` (`db/migrations/025_session_purpose.sql:16-28`) and is the live session table referenced by `attempt`, `selection_log`, `competency_gap`, etc. (`db/schema.sql:421-433`).
7. `schema_migration` exclusion: created at runtime by `backend/app/migrate.py:14` with **3 columns** (`version`, `checksum`, `applied_at`), and explicitly excluded from introspection/test comparisons in `backend/tests/test_migrations.py:99-120,191`, `backend/tests/test_migrations_026.py:53-69`, `backend/tests/test_migrations_027.py:24-40`, and `backend/tests/test_final_acceptance.py:216`. This explains "live DB 68 tables / 564 columns" vs documented 67/561.
8. Traceability verification: parsed all 67 table rows of `docs/submission/final/TRACEABILITY.md` and compared each column count with the introspection JSON — **67 rows, 0 mismatches**.

**Conclusion:** 67/561/122/159/28 are correct for the versioned schema; 68 `CREATE TABLE` statements, 0 enum types, and the runtime-only `schema_migration` table are important nuances that the docs state only implicitly or via owner questions (`docs/agent/freeze-logs/doc-verify.md:100-102,148-149`).

---

## 3. API (OpenAPI)

- Committed contract: `docs/openapi.json`; exporter/verifier `scripts/export_openapi.py:11-25` (read-only `--check` compares rendered JSON). Saved check log: `docs/agent/freeze-logs/openapi-check.log` ("OpenAPI matches the runtime contract"; also shows benign warnings about unknown `LLM_PROVIDER=Mistral` and development JWT secret).
- Parsed `docs/openapi.json` with PowerShell `ConvertFrom-Json`: **106 paths / 118 operations** — identical to `docs/diagrams/schema-028/manifest.json:583-584`.
- Router modules contributing paths (7): `auth`, `oauth`, `admin`, `assessments`, `concepts`, `sessions`, `practice`; plus three app-level paths `/health`, `/api/v1/ping`, `/readiness` (`backend/app/main.py:78-93`).
- Auth endpoints (**12 paths**): `/api/v1/auth/{register,login,refresh,logout,me,renew,password-reset/request,password-reset/confirm,oauth/providers,oauth/complete,oauth/{provider}/start,oauth/{provider}/callback}`.
- Role enforcement: `backend/app/deps.py:19-86` defines `Learner`, `Administrator`, `require_roles`, `LearnerOnly`, `AdminOnly`, `RoleManagerOnly`; `backend/app/openapi.py:29-44` publishes `x-required-roles`/`x-role-manager` on protected operations. Parsed contract: **101 operations carry `x-required-roles`**. Usage counts in routers: admin.py 66, sessions.py 26, practice.py 11, assessments.py 3, auth.py 3, concepts.py 2 dependency references.
- Uniform error envelope and shared status codes are injected into the contract by `backend/app/openapi.py:18-59`; runtime handlers in `backend/app/errors.py:36-94`.

---

## 4. Auth / authorization

- JWT: bcrypt password hashing and HS256 JWT issue/verify in `backend/app/security.py:19-84`. Access tokens carry `typ`, `auth_time`, `pwd_at`, `sub`, `roles`, `iat`, `exp`, optional `sid` (`security.py:40-70`). Defaults `JWT_SECRET=change_me_jwt_secret`, 60-minute access, 480-minute session, 7-day refresh (`backend/app/config.py:28-32`); dev-default secret warns at startup (`backend/app/main.py:19-23`).
- Per-request guard: `backend/app/deps.py:27-58` verifies Bearer token, active account, `pwd_at` credential epoch (password reset invalidates old tokens) and refresh-family revocation. Role guards at `deps.py:61-86`; role management is a separate `can_manage_roles` capability, not implied by Administrator.
- OAuth: Google/GitHub authorization-code flow with state and handoff cookies — `backend/app/routers/oauth.py:63-154`, `backend/app/services/oauth.py` (state/handoff JWT purposes at `services/oauth.py:176,195,243,270`), config at `backend/app/config.py:111-129` (empty client id disables a provider with 503 `oauth_not_configured`). Frontend `frontend/src/components/OAuthButtons.jsx`, `frontend/src/pages/OAuthCallbackPage.jsx`; e2e `frontend/e2e/oauth.spec.js`.
- Password reset / OTP-like flow: `backend/app/routers/auth.py:97-173`, `backend/app/services/password_reset.py`, SMTP/Mailpit config `backend/app/config.py:131-150`; token TTL 15 min, hashed tokens, request/confirm/IP rate limits. Frontend `ForgotPasswordPage.jsx`, `ResetPasswordPage.jsx`.
- Login throttling: `backend/app/services/login_throttle.py` (5 attempts / 300 s per email+IP; `config.py:35-40`).
- Refresh sessions: `backend/app/services/refresh_tokens.py`, table `refresh_session`.

---

## 5. Workflows

- **Practice vs TEST sessions:** authoritative distinction in `db/migrations/025_session_purpose.sql:1-45` — "TEST sessions are scored tests; PRACTICE sessions are learning evidence"; `assessment_session.purpose IN ('TEST','PRACTICE')` with `purpose_source IN ('SERVER','BACKFILL')` (CHECK constraints at `:49-69`). Selection logic: `backend/app/services/practice_service.py:327` sets `TEST` for FIXED/ADAPTIVE styles else `PRACTICE`; `backend/app/services/personalized_assessment.py:283`; provenance only counts server-created TEST sessions (`backend/app/services/cumulative_competency.py:17`). Official result versions apply only to server-created FIXED TEST sessions (`backend/app/services/result_version.py:35-54`).
- **AI mode 1 vs mode 2:** `frontend/src/pages/AssessmentsPage.jsx:104-105` — "Mode 1 uses the reviewed bank; mode 2 uses live AI questions, one concept and one starting band." Backend `backend/app/services/practice_service.py:41,100-101,255-307` (`source: "bank" | "ai"`, provider failures fall back to the reviewed bank) and `backend/app/services/ai_adaptive.py:1` ("Mode 2: live AI questions inside an adaptive practice session"). Free plan hides Mode 2 (`AssessmentsPage.jsx:52-54,106-108`).
- **AI pipeline:** AI #1 prompt builder — `backend/app/services/prompt_builder.py:1,14-24` ("AI #1 builds prompts only"; `VERSION="two-ai-v4"`, 6 prompt sections, structured output fields reserved for the evaluator). AI #2 evaluator — `backend/app/services/evaluation_pipeline.py:1,11-56` ("strict evidence-based JSON with an explicit deterministic fallback", learner-text sanitisation, coverage and score-range validation). Provider abstraction: `backend/app/services/llm/{provider,sanitize,validation,errors,service}.py`; model/cache config in `backend/app/config.py:152-189`.
- **Grading / review / approval / release:** `backend/app/services/grading_jobs.py` (durable claims, bounded retries), `grading_service.py`, `essay_grading.py`, `sql_grading.py`; `backend/app/services/grading_review.py:23-86` — `is_published()` requires `release_status == "published"`, `reconcile()` moves sessions through `auto_grading`, `pending_review`, `reviewed`, `provisional_ai`, `grading_failed`, `published`, and `transition()` writes an auditable `ResultReleaseEvent` with server clock. Human verification is driven by `result_release_policy` (`HUMAN_VERIFIED` vs `IMMEDIATE`), with admin review endpoints under `/api/v1/admin/grading-reviews/...` and `/api/v1/admin/review-requests/...` (`docs/openapi.json`). Result versions/evidence/publication live in the 026 tables (`backend/app/services/result_version.py`, migration `db/migrations/026_pr3a_database_foundation.sql`); review flow in migrations 027/028 and `backend/app/services/review_flow.py`, `review_regrade.py`.
- **Free/Pro UI demo gating:** `frontend/src/demo/freePro.jsx:5-47` — `DEMO_FREE_SESSIONS=5`, `DEMO_PRO_PRICE_VND=99000`, `DEMO_PRO_DAYS=30`, localStorage key `dbcas_demo_plan`, flag `VITE_DEMO_FREE_PRO` (default on, explicit `'false'` disables). Consumed by `frontend/src/pages/AssessmentsPage.jsx` (gates Mode 2), `DashboardPage.jsx`, `AdminPage.jsx` (admin-only static cost panel). Purely client-side simulation — no backend entitlement checks. E2E `frontend/e2e/demo-free-pro.spec.js` (runs only with `DBCAS_DEMO_FREE_PRO=1`); note its expected string "Free ≥ 3 sessions per month" is stale relative to the code's 5 sessions/day.
- **Question caps:** `backend/app/services/practice_config.py:4-20` — min 1, default 5, legacy max **13**, single-type caps MCQ **50** / SQL **5** / essay **10**, mixed caps MCQ 20 / SQL 2 / essay 3, mixed total **25**. Enforced by Pydantic validators `backend/app/services/practice_service.py:53-127`; mirrored in the UI `frontend/src/assessmentStyle.js:14-18`; exposed via `/api/v1/practice/options`. Therefore any claim that the implemented cap is "1–20 questions" is wrong; 20 is only the mixed-MCQ per-type cap.

---

## 6. Validation, integrations, CI/CD

- Request/response validation: Pydantic models in `backend/app/schemas.py`, `schemas_analytics.py`, `schemas_operational.py`, plus per-service models (e.g. `PracticeStart` in `practice_service.py:37-140`). `RequestValidationError` → 422 `validation_error` with loc/type/msg details (`backend/app/errors.py:78-94`). Uniform `{"error":{"code","message","details"}}` envelope for all handlers (`errors.py:29-93`).
- LLM provider config: `backend/app/config.py:152-228` — one OpenAI-compatible provider; unknown `LLM_PROVIDER` values are accepted and reported as `openai_compatible` (warning, not failure), empty key disables AI gracefully (`llm_not_configured`), HTTPS required outside development, bounded retries/timeouts. See also `scripts/llm-check.mjs`, `scripts/real-provider-qa.mjs`.
- Root `package.json:6-29` scripts: `start`, `demo:snapshot`, `env:check`, `llm:check`, `secrets:scan`, `test:secrets`, `stop`, `reset`, `test:local`, `test:smoke`, `test:qa`, `diagrams:check`, `diagrams:render`, `docs:check`, `docs:render`, `diagrams:setup`, `ui:contrast`, `inventory:check`, `inventory:write`, `docs:verify-word`, `docs:build`, `docs:finalize`, `docs:verify-word:v12`. Pinned dev deps `@mermaid-js/mermaid-cli 12.2.0`, `@viz-js/viz 3.31.0`.
- Frontend `package.json:9-20` scripts: `dev`, `build`, `lint`, `format`, `format:check`, `brand:icons`, `preview`, `test`, `test:e2e`, `test:practice`, `test:local`.
- CI `.github/workflows/dn-backend.yml` ("Local quality gate", triggers push/PR on `develop2` and `main`): **6 job definitions** — `changes`, `secrets`, `backend`, `frontend-static`, `frontend-shard`, `frontend-local`. `frontend-shard` matrix has **9 legs**: e2e-1 (localization), e2e-2/e2e-3 (rest, shards 1/2 and 2/2), qa-1/qa-2/qa-3, smoke-1/smoke-2/smoke-3 (`dn-backend.yml:166-267`). Fan-in `frontend-local` checks exactly 9 shard artifacts (`:375-408`). Executed jobs = 5 singleton + 9 matrix = **14**. Other workflows: `.github/workflows/demo-seed-benchmark.yml` job `measure`; `.github/workflows/qa-oom-repro.yml` job `repro` (not part of the 14).
- Saved evidence `docs/agent/freeze-logs/final-ci-conclusion.log` parses as `conclusion=success`, `headSha=d6df804e831c0c69771a5ecd744b2defe5cc3403`, run `45597486074`, **14 jobs, 14 successful**. Caveat: current HEAD is `66045b7`, **16 commits after `d6df804`** (all docs-only per `git log`); the CI result is for that earlier commit, not HEAD.

---

## 7. Security-related implementation and known limitations

- SQL sandbox: read-only by default via role `learner_ro` and `default_transaction_read_only` check (`backend/app/config.py:42-65`, `backend/app/services/sandbox_runner.py:769-773`); statement timeout ≤ 3000 ms, row/byte/cell caps (`config.py:56-62`); SQL classification/validation in `backend/app/services/{sql_classifier,sql_validator,sql_service}.py`. Ephemeral container mode uses `--network none`, 256 MB memory/swap, 1 CPU, uid/gid 10001 (`backend/app/services/ephemeral_sandbox.py:139-148`); Dockerfiles in `sandbox/`.
- **All multi-statement/writable features are default OFF** (`backend/app/config.py:67-78`): `SANDBOX_MULTI_STATEMENT`, `SANDBOX_WRITABLE`, `GRADING_STATE_MODE`; `SANDBOX_WRITABLE` additionally requires `SANDBOX_MODE=ephemeral` (`config.py:233-236`).
- **Broker is default OFF** (`SANDBOX_BROKER=False`, `config.py:80-109`): validation only runs when enabled (`backend/app/main.py:29-31`); `backend/app/services/broker/service.py:23-62` validates a locked-down container template (`network=none`, `read_only_root`, `uid/gid 10001`, `cap_drop ALL`, `no_new_privileges`, `pids_limit 128`, 256 MB, 1 CPU), HMAC capability tokens with 300 s TTL, dataset/image digest allow-lists, and rejects writable mode. Runtime defaults to `"stub"` — never executes real SQL. Known limitation documented in `docs/analysis/broker-validation.md:3-5`: no real broker runtime probe has been enabled in CI; B2 (separate service) and B3 (writable) remain preconditions.
- Deployment safety: `backend/app/services/deployment_safety.py:7-14` fails startup outside development if known demo passwords remain; `config.py:230-271` rejects weak JWT secrets, demo credentials in staging/production, shared app/sandbox DB servers, non-HTTPS origins, Mailpit SMTP, and non-ephemeral writable SQL. Production is **HOLD** in `docs/agent/STATUS.md:30,70`, `docs/agent/BACKLOG.md:54,78`, `docs/demo/README.md:3,85` — no release deployment is claimed; `docker-compose.release.yml` is release-shaped but not deployed (`docs/architecture/DECISIONS-FINAL.md:73,84`).
- Env hygiene: `.env` ignored/untracked, only `.env.example` committed; secret scanner `scripts/scan_secrets.py` with allowlist `scripts/secret_scan_allowlist.json`.
- Known limitations from `docs/agent/freeze-logs/doc-verify.md:151-157`: two-stage AI audit and writable DML path were not re-executed for the ver1.3 document set; no learner/usability study; PDF page evidence comes only from the Word export (LibreOffice/Poppler absent). Additionally, the four ephemeral-sandbox tests are environment-sensitive on this Windows host (`docs/agent/freeze-logs/pytest-environment-limitation.log:1-34`).

---

## 8. Testing counts and evidence

### Static counts (no suite run)
| Item | Count | Method / source |
|---|---:|---|
| Pytest modules, top level `backend/tests/test_*.py` | 94 | `Get-ChildItem backend\tests\test_*.py` |
| Pytest contract modules `backend/tests/dn/` | 24 | directory listing (`test_bank_contracts.py` … `test_statistics_api.py`) |
| Pytest modules total (recursive) | 118 | 94 + 24; `Get-ChildItem ... -Recurse -Filter test_*.py` |
| Static test functions (`def test_`) | 1,139 (1,019 top-level + 120 dn) | regex over all `test_*.py`; parametrization expands this to the collected count |
| Vitest files under `frontend/src/` | 54 | recursive include `*.test.js(x)`, `*.spec.js(x)` |
| Static `it(`/`test(` calls in those files | 384 | regex count |
| Playwright specs `frontend/e2e/*.spec.js` | 25 | directory listing + `docs/agent/freeze-logs/final-e2e-shards.log:1-2` ("all 25 e2e specs assigned exactly once") |

### Saved logs vs claims
| Claim (`SOURCE_CODE.md` §5 / `doc-verify.md` §4, §7) | Saved repo evidence | Status |
|---|---|---|
| Backend lint PASS | `docs/agent/freeze-logs/backend-lint.log` ("All checks passed!") | **Cited** |
| Backend tests **1,940 passed, 7 skipped**, exit 0 | `docs/agent/freeze-logs/backend-pytest-final.log:35` — `1940 passed, 7 skipped ... 1434.00s (0:23:54)`; also `baseline-backend-pytest.log:35` (1,438.70 s) | **Counts cited; duration "24 min 22 s" / 1,462.64 s is uncited** (only `docs/submission-pack/SUMMARY.md:35`). `pytest-environment-limitation.log:33` says **1,945** passed — internal inconsistency. `backend-pytest-full.log:233` shows an earlier 5 failed / 1,934 passed run. |
| Frontend unit tests 54 files / 463 tests | `docs/agent/freeze-logs/frontend-test.log:16-17`, `baseline-frontend-unit.log:10-11` | **Cited** |
| Frontend lint / format PASS | `docs/agent/freeze-logs/frontend-lint.log`, `baseline-frontend-lint.log`, `baseline-frontend-format.log`; CI `frontend-static` | **Cited** |
| Browser suites **152 passed, 4 skipped** | `baseline-e2e-1-localization.log` 11 passed; `baseline-e2e-2-rest.log` 36; `baseline-e2e-2-rest-shard2.log` 36; `baseline-practice.log` 12; `baseline-local-smoke.log` 3; `baseline-qa.log` 54 → **152 passed**; `final-e2e-shards.log` only proves assignment | **"152 passed" supported; "4 skipped" not present in any saved log — unsupported** |
| API contract 106 paths / 118 operations, check PASS | `docs/agent/freeze-logs/openapi-check.log`; `docs/openapi.json` | **Cited** |
| Route inventory PASS | `docs/agent/freeze-logs/baseline-inventory-check.log` ("OK: api-routes.json and frontend-routes.json match their sources") | **Cited** |
| Secret scan, whole tree, 0 findings, **3,129 files** | `baseline-secrets-tree.log:5` = **3,050** files; `final-secrets-tree.log:5` = **3,083** files; both 0 findings | **0 findings cited; file count 3,129 unsupported by any saved log** |
| Submission docs 5 documents, **149 assertions, 0 failures** | `docs/submission/final/verification/verification-report.md:3` (149 assertions, 0 failures, full 149-row report) | **Cited** |
| Documentation gate PASS, **48 assertions, 67/561/122/159/28** | `docs/agent/freeze-logs/{docs-check,baseline-docs-check,final-docs-check}.log` all print `docs:check: 48 assertions, tables=67, columns=561, fks=122, indexes=159, migrations=28, ...` | **Cited** |
| Exact-commit CI **14/14 success** at `d6df804`, run 45597486074 | `docs/agent/freeze-logs/final-ci-conclusion.log` (JSON: conclusion success, 14 jobs, all success) | **Cited, but applies to an older commit (16 behind HEAD)** |
| Clean clone + readiness | `docs/submission/final/verification/clean-clone.log` (`npm ci`, `env:check`, `start` EXIT=0; readiness `database:true, sandbox:true`) | **Cited** |
| verify_docx gate | `docs/agent/freeze-logs/final-docs-check.log:27` = `verify_docx: 52 assertions, 0 failures` (a different verifier from `verify_submission_docs.py`'s 149) | **Cited; two different assertion counts should not be conflated** |

---

## Traceability matrix

| Row | Documentation claim (source) | Implementation evidence (path) | Verified / Outdated / Unverifiable | Required action |
|---|---|---|---|---|
| Architecture | "8 router modules" (`SOURCE_CODE.md:61`) | `backend/app/main.py:15,69-75`; `backend/app/routers/*.py` | **Outdated (counting convention)** — 7 routers registered; 8 `.py` files only because `__init__.py` is counted | State "7 router modules (8 `.py` files including `__init__.py`)" |
| Architecture | "73 service modules" (`SOURCE_CODE.md:62`) | `backend/app/services/*.py` (72 excl. `__init__.py`, 73 incl.); `services/broker/` (6), `services/llm/` (5) | **Outdated (counting convention)** — 83 real modules including subpackages | State the convention explicitly; give 72 top-level + 11 subpackage modules |
| Architecture | "13 repository classes", "models.py 67 tables" (`SOURCE_CODE.md:63-64`) | `backend/app/repositories.py` (13 `class` at lines listed); `backend/app/models.py` (67 `__tablename__`) | **Verified** | None |
| Architecture | Frontend "React 19 + Vite", "54 vitest files" (`SOURCE_CODE.md:66-67`) | `frontend/package.json:22-47`; `frontend/src/` enumeration | **Verified** | None |
| Architecture | Deployment assets `deploy/`, sandbox image (`SOURCE_CODE.md:72-73`) | `deploy/nginx.conf`, `deploy/release.env.example`; `sandbox/Dockerfile`, `Dockerfile.ephemeral`; 9 Compose files | **Verified** | None |
| Database | "67 tables, 561 columns, 122 FKs, 159 indexes, 28 migrations" (`TRACEABILITY.md:38-108`, `doc-verify.md:88-92`, `SOURCE_CODE.md:106`) | `docs/diagrams/schema-028/schema-introspection.json` (PG 17.12); `manifest.json:3-8`; `db/migrations/*.sql` (28) | **Verified** (67 distinct tables; 68 `CREATE TABLE` statements because `concept_dependency` is created twice) | Add a one-line note about 68 DDL statements / 67 distinct tables |
| Database | "schema_migration excluded; live DB 68 tables / 564 columns" (`doc-verify.md:100-102`) | `backend/app/migrate.py:14` (3 columns); `backend/tests/test_migrations.py:99-120` | **Verified** | None |
| Database | "legacy `assessment*` tables" (`doc-verify.md:148-149`) | `manifest.json:518-523` + `scripts/check_docs.py:156-164`: exactly 4 (`assessment`, `assessment_blueprint`, `assessment_concept`, `assessment_question`); `assessment_session` is live | **Verified (with nuance)** | Say "four legacy tables"; do not imply `assessment_session` is retired |
| Database | Enum types | `db/schema.sql` `CREATE TYPE` → 0; `manifest.json:7` `enums: 0` | **Verified: zero enums** (not claimed explicitly) | No change unless a doc asserts enum types exist |
| API | "106 paths / 118 operations, check PASS" (`SOURCE_CODE.md:102`, `doc-verify.md:93-94`) | `docs/openapi.json` parsed; `scripts/export_openapi.py`; `docs/agent/freeze-logs/openapi-check.log` | **Verified** | None |
| API | Auth endpoints and role-based access (`doc-verify.md` FR coverage) | `backend/app/routers/auth.py`, `oauth.py`; `backend/app/deps.py:19-86`; `backend/app/openapi.py:29-44` (101 operations with `x-required-roles`) | **Verified** | None |
| Workflow | Practice vs TEST purpose | `db/migrations/025_session_purpose.sql:1-69`; `backend/app/services/practice_service.py:327`, `cumulative_competency.py:17`, `result_version.py:35-54` | **Verified** | None |
| Workflow | AI mode 1 (bank) vs mode 2 (live AI); prompt builder + evaluator | `frontend/src/pages/AssessmentsPage.jsx:104-105`; `backend/app/services/practice_service.py:41,255-307`; `prompt_builder.py:1`; `evaluation_pipeline.py:1`; `services/llm/` | **Verified** | None |
| Workflow | Grading/review/approval/release, result publication | `backend/app/services/grading_review.py:23-86`; `grading_jobs.py`; `result_version.py`; migrations 026-028 | **Verified** | None |
| Workflow | Free/Pro demo gating (`free-pro-design.md`, demo specs) | `frontend/src/demo/freePro.jsx:5-47`; `AssessmentsPage.jsx:52-54,106-108` | **Verified (client-side only)** | Keep "UI simulation, no backend entitlements"; fix stale E2E string "3 sessions per month" → 5/day |
| Workflow | "1–20 questions" flagged as obsolete term (`doc-verify.md:106-108`, verification report :88,104,112,120) | `backend/app/services/practice_config.py:4-20` (legacy max 13; single MCQ 50; mixed total 25) | **Verified as a document-term sweep; implementation caps are different** | If any document describes the implemented cap as 1–20, correct it (e.g. "13 legacy / up to 50 single-type MCQ / 25 mixed") |
| CI/CD | "14 of 14 jobs successful", 5 singleton + 3×3 shards (`SOURCE_CODE.md:107-111`, `doc-verify.md:126-132`) | `.github/workflows/dn-backend.yml:14-408` (6 job defs, 9 matrix legs); `docs/agent/freeze-logs/final-ci-conclusion.log` (14/14, `d6df804`) | **Verified for `d6df804`; stale for HEAD `66045b7`** | Retain log and state the commit; do not imply HEAD was CI-verified |
| CI/CD | `docs:check`, `docs:verify-word`, `docs:build`, `docs:finalize`, `inventory:check`, `secrets:scan` scripts | `package.json:6-29` | **Verified** | None |
| Testing | 94 pytest modules + 24 dn, 54 vitest files, 25 Playwright specs (`SOURCE_CODE.md:65-68`) | `backend/tests/` enumeration; `frontend/src/` enumeration; `frontend/e2e/*.spec.js`; `final-e2e-shards.log:1-2` | **Verified** | None |
| Testing | "1,940 passed, 7 skipped (24 min 22 s)" (`SOURCE_CODE.md:98`, `doc-verify.md:95`) | `docs/agent/freeze-logs/backend-pytest-final.log:35` (1,940/7 in **0:23:54**); `pytest-environment-limitation.log:33` says 1,945 | **Partially verified / inconsistent** — counts cited, duration uncited, one internal contradiction | Cite the exact log path; drop or correct "24 min 22 s"; reconcile 1,940 vs 1,945 |
| Testing | "152 passed, **4 skipped**" browser suites (`SOURCE_CODE.md:101`, `doc-verify.md:97`) | Six baseline shard logs sum to 152 **passed**, no skips anywhere; `final-e2e-shards.log` only shows assignment | **Unverifiable / unsupported (4 skipped)** | Remove "4 skipped" or save the missing shard logs |
| Testing | "Secret scan whole tree, 0 findings (**3,129 files**)" (`SOURCE_CODE.md:104`, `doc-verify.md:98,131`) | `baseline-secrets-tree.log:5` = 3,050; `final-secrets-tree.log:5` = 3,083; both 0 findings | **Outdated / unsupported file count** | Replace with "3,083 files at last saved run" or quote only "0 findings" |
| Testing | "149 assertions, 0 failures" (`doc-verify.md:49-50,129`, `SOURCE_CODE.md:105`) | `docs/submission/final/verification/verification-report.md:3-155` | **Verified** | None |
| Testing | "48 assertions, 67/561/122/159/28" docs gate (`doc-verify.md:128`) | `docs/agent/freeze-logs/{docs-check,baseline-docs-check,final-docs-check}.log` | **Verified** | None |
| Security | SQL sandbox, default-OFF writable/multi-statement flags (`SOURCE_CODE.md:18-20`) | `backend/app/config.py:42-78,233-236`; `services/sandbox_runner.py:769-773`; `services/ephemeral_sandbox.py:139-148` | **Verified** | None |
| Security | Broker behind default-OFF flag (`doc-verify.md:153-154`, analysis docs) | `backend/app/config.py:80-109`; `backend/app/main.py:29-31`; `services/broker/service.py:23-62`; `docs/analysis/broker-validation.md:3-5` | **Verified** — flag OFF, runtime `stub`, no CI runtime probe | None |
| Security | Production HOLD, no deployment claimed (`doc-verify.md` §8-9, `STATUS.md`) | `docs/agent/STATUS.md:30,70`; `docs/demo/README.md:3,85`; `services/deployment_safety.py:7-14`; `config.py:230-271` | **Verified** | None |

---

## Explicitly flagged discrepancies

1. **Fabricated/stale number — secret-scan file count.** `3,129 files` (`SOURCE_CODE.md:104`, `doc-verify.md:98,131`, `SUMMARY.md:42`) has no saved log; saved logs show 3,050 and 3,083. The "0 findings" part is genuine.
2. **Unsupported number — "4 skipped" browser tests** (`SOURCE_CODE.md:101`, `doc-verify.md:97`). No saved log contains skips for the browser suites; only the 152 passed total is evidenced.
3. **Inconsistent test count/duration.** `1,940 passed, 7 skipped` is in `backend-pytest-final.log` but at **23:54**, not "24 min 22 s"; `SUMMARY.md:35` states 1,462.64 s; `pytest-environment-limitation.log:33` states **1,945** passed. Only the 1,940 figure has a matching saved log.
4. **Counting-convention drift (not fabrication).** "8 router modules" and "73 service modules" are file counts that include `__init__.py` and (for services) exclude the `broker/` and `llm/` subpackages. Runtime reality: 7 routers, 72 top-level service modules, 83 including subpackages.
5. **CI evidence applies to an older commit.** `d6df804` is 16 commits behind current HEAD `66045b7` (docs-only commits). The 14/14 result is real but must be attributed to that commit.
6. **Two different verifier assertion counts.** `verify_submission_docs.py` → 149 assertions (`verification-report.md`); `scripts/verify_docx.py` → 52 assertions (`final-docs-check.log:27`). Both are real; do not merge them.
7. **Minor stale UI/E2E string.** `frontend/e2e/demo-free-pro.spec.js` expects "Free ≥ 3 sessions per month" while `frontend/src/demo/freePro.jsx:5,58,90` defines 5 sessions/day; that spec is skipped unless `DBCAS_DEMO_FREE_PRO=1`.
8. **DDL nuance.** 68 `CREATE TABLE` statements vs 67 tables (`concept_dependency` at `db/schema.sql:83` and `:440`); 0 enum types. Documentation's 67/561/122/159/28 numbers remain correct for the distinct-table schema.

**Overall:** the core quantitative claims (67/561/122/159/28, 106/118, 13 repositories, 67 ORM tables, 94+24 pytest modules, 54 vitest files, 25 e2e specs, 12 auth paths, 101 role-protected operations, 14 CI jobs at `d6df804`, 48/149 gate assertions) are **verified against source or saved artifacts**. The discrepancies above are confined to counting conventions, one unverified browser-skip figure, one stale file-count figure, one duration/count inconsistency, and commit attribution of CI evidence.
