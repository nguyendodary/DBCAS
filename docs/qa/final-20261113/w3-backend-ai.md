# W3 — Backend and AI final audit

Worktree: `_worktrees/dbcas-dn-20261101` (branch `develop2`)
Baseline HEAD: `28c1784` — `docs(qa): open final audit status table`
Audit date: 2026-11-11 (report identifier `20261113`)

Scope: API contract vs OpenAPI/inventory, error envelope, JWT/refresh security,
auth and AI throttling, SQL sandbox isolation, Prompt Builder purity, evaluator
prompt identity, caching/timeouts/fallback, exact-count practice assembly,
bank validation, migration idempotency, log/secret hygiene, dependency audit,
dead code, and the optional live provider.

No commit or push was made. No `.env` value was printed. No live provider call
was made in this workstream. No Docker demo stack was rebuilt or restarted;
the disposable PostgreSQL/sandbox containers were those created by the existing
`backend/tests/conftest.py` fixture.

## Checklist

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Static route inventory vs runtime OpenAPI | **PASS (defect D1 fixed)** | `docs/inventory/api-routes.json`: `count=92`, 92 unique method/path entries; `docs/openapi.json`: 82 paths / 92 operations; runtime `app.openapi()` deep-equal on all operations and 128 component schemas; `scripts/export_openapi.py --check` PASS; `npm run inventory:check` PASS. Response-model audit: 92/92; status audit: 92/92. |
| 2 | Error envelope: no stack traces/secrets; 4xx/5xx consistency | **PASS** | `backend/app/errors.py:44-94`; probe `w3/error-envelope-probe.log` produced 500/409/404/422 with no `Traceback`, DSN, or submitted-value marker. Application-facing failures use `AppError`; OAuth and LLM internals normalize their own errors before the envelope. No ad-hoc `HTTPException` raise was found in `backend/app` (only the handler imports Starlette's class). |
| 3 | JWT access/refresh rotation, replay rejection, logout family revocation | **PASS** | `backend/app/security.py:40-84`, `backend/app/services/refresh_tokens.py:55-90`, `backend/tests/dn/test_refresh_tokens.py`: 7/7 passed. Replay of a consumed refresh token revokes the family; the rotated access token then gets 401; logout is idempotent and revokes both refresh and live access. |
| 4 | Auth rate limiting | **PASS** | `backend/app/services/login_throttle.py:55-181`; in-process fake-clock suite `tests/test_login_throttle.py` 12/12; DB-atomic throttle coverage in `tests/test_shared_auth.py` (part of the 98-test auth batch). 429 responses carry `Retry-After`; disabled accounts do not consume credential-failure quota. |
| 5 | AI rate limiting / cost quota | **PASS for documented translation quota; ASK for practice generation** | `backend/app/services/question_translation.py:30-56,121` implements 2 requests/admin/minute and 20/hour per process, 429 + `Retry-After`; `tests/test_question_translation_draft.py` 14/14 (quota test in the 48-test translation batch). `POST /practice/start` with `source=ai` calls the provider up to twice per start with only the 10 s/0-retry budget (`routers/practice.py:43-50`, `services/practice_generation.py:352-418`); there is no per-user limiter. No documented AI quota exists for that flow, so this is reported as an architectural ASK, not changed. |
| 6 | SQL sandbox isolation and SELECT-only enforcement | **PASS** | `services/sql_validator.py:124-193`, `services/sandbox_runner.py:164-276`, `services/ephemeral_sandbox.py`. Sandbox suites: 141/141 passed (`test_sandbox_safety.py`, `test_sandbox.py`, `test_sandbox_protocol.py`, `test_sandbox_connections.py`) plus 4/4 real disposable-container tests (`tests/dn/test_ephemeral_sandbox.py`). Extended probe `w3/sql-validator-probe.log`: multi-statement INSERT, DROP, UPDATE, CREATE, `SET search_path`, `set_config`, catalog reads, `FOR UPDATE`, `SELECT INTO`, and `COPY` all rejected; a safe CTE SELECT allowed. |
| 7 | Role checks and ownership | **PASS** | `backend/app/deps.py:27-86`; `tests/test_rbac.py` 6/6; forged Administrator token claim is rejected by the DB role read (`test_final_acceptance.py:96-106`, part of 111 contract/acceptance tests). Cross-learner session/evidence/SQL paths use 404 ownership guards (`session_guard.py:14-35`). |
| 8 | Prompt Builder purity: one finished-attempt prompt, never grades | **PASS** | `services/prompt_builder.py:92-170` rejects preamble, extra/missing sections, changed data/schema, output-only keys, feedback markers, grades, and copied answers. `tests/test_ai_pipeline_purity.py` 15/15. The builder does not mutate input. |
| 9 | Evaluator receives the byte-identical built prompt | **PASS** | `services/evaluation_pipeline.py:127-157` sanitizes before build, hashes that prompt, and passes `sanitize_messages=False`. `tests/test_ai_prompt_hash.py` 10/10. Direct fake-provider probe `w3/prompt-evaluator-probe.log`: builder called once, evaluator called once, evaluator message == `build_prompt(data).prompt`, and SHA-256 matched (`2b4d11e6…`). No real key used. |
| 10 | Caching, timeout, fallback | **PASS** | `services/llm/service.py:98-155,238-259`, `services/llm/provider.py:164-252`; `tests/test_llm.py` 39/39; `tests/test_ai_prompt_hash.py` 10/10. Cache hit made one provider call; invalid output was not cached; timeout and malformed output fell back to rules; 429/5xx retried within the configured budget. |
| 11 | Exact-count guarantee and bank fallback | **PASS** | `services/practice_bank.py:66-112`, `services/practice_selection.py:77-172`; exhaustive matrix `tests/dn/test_practice_matrix.py`: **2,291,100 cases, 0 failed**, 3,241 scopes × 7 difficulty subsets × 20 counts × 7 source modes; 31/31 recovery tests; partial/provider-failure/timeout/overflow all retained the requested count. |
| 12 | Terminal auth failure is not retried | **PASS** | `tests/dn/test_generation_auth_failures.py` 2/2: `LLMError.AUTH_FAILED`/`NOT_CONFIGURED` produce one provider call and then bank/template recovery. `tests/test_llm.py:130-140` separately proves HTTP 401 is one attempt with no retry. |
| 13 | Bank integrity validator | **PASS** | `app/validate_bank.py` + `services/question_validator.py:225-245`: 5,482 questions (2,006 MCQ, 1,747 SQL, 1,729 essay), **0 invalid**, empty failure map. Static run only (`sql_execution: not executed`); SQL execution is covered by the 178 SQL/sandbox tests. |
| 14 | DB constraints and migration idempotency | **PASS** | `tests/test_migrations.py` 8/8 and `tests/dn/test_database_initialization.py`/bank contract tests total 23/23. 19 migration files; fresh/pre-OAuth/post-OAuth/current matrix repeated, second `apply_migrations()` returned `[]`, data preserved, upgraded shape equals fresh schema. No migration was added or edited. |
| 15 | Logs free of secrets | **PASS** | `scripts/audit_secret_hygiene.py`: 5,535 reachable Git blobs plus tracked files, **0 history/tracked findings**, `pass=true`; ignored env files hold 5 secret values, never printed. Log assertions in `tests/test_ai_prompt_hash.py` and `tests/dn/test_practice_recovery.py` prove no prompt/answer/provider message is logged. W3 logs: 0 key/bearer/password patterns. |
| 16 | Dependency audit | **PASS with 2 low root dev advisories** | Backend runtime `pip-audit`: 35 dependencies, **0 vulnerabilities**; dev requirements: 40 dependencies, **0**. Frontend `npm audit`: **0** of any severity (285 dependencies). Root dev toolchain: **2 low / 0 moderate / 0 high / 0 critical** (`@mermaid-js/mermaid-cli` via `katex`; dev-only, fix is a pinned tool upgrade). `pip check`: no broken requirements. |
| 17 | Dead-code scan | **PASS (informational)** | `ruff --select F401,F811,F841,F821`: 27 findings = 24 unused imports + 3 unused locals (`adaptive_engine.py:250` `seq_no`, `grading_review.py:137` `manual_fallback`, `practice_bank.py:68` `known`). No behavioral defect found and no code removed. `ai/` had no findings. |
| 18 | Backend lint/build | **PASS** | `ruff check app ../ai` exit 0; `python -m compileall -q app` PASS; `pip check` PASS; frontend `npm run lint` PASS (auxiliary). |
| 19 | Live provider | **SKIP (external 403)** | Key is configured (boolean check only), but **0 real calls were made this round**. The prior audited live ledger used **3/5** requests, all HTTP **403** before a completion; do not retry. Fake `httpx.MockTransport` paths are the verified path. No key, header, prompt, or response body was printed or saved. |

## Defect fixed

### D1 — Route inventory omitted response models for app-level routes

| Item | Detail |
| --- | --- |
| Symptom | `docs/inventory/api-routes.json` recorded `"response_model": ""` for `GET /health`, `GET /api/v1/ping`, and `GET /readiness`, although `docs/inventory/README.md` says the file records each route's response model and runtime OpenAPI has `StatusResult`, `PingResult`, and `ReadinessResult`. |
| Root cause | `scripts/generate_route_inventory.py` had a separate `main.py` branch with `"response_model": ""` hardcoded. The router branch also selected the first route decorator by method only rather than the decorator matching the emitted method/path. |
| Fix | `decorators()` now yields the matched decorator together with method/path; both the router and `main.py` branches call `response_model(decorator)`. Regenerated `docs/inventory/api-routes.json`; only the three missing fields changed. |
| Files | `scripts/generate_route_inventory.py:55-110`, `docs/inventory/api-routes.json` (three fields), `backend/tests/dn/test_openapi_contract.py:52-60`; exact patch in `w3/our-diff.patch`. |
| Regression | New `test_generated_inventory_records_response_models_for_main_app_routes` fails on the baseline with `assert '' == 'StatusResult'` (`w3/inventory-response-model-before.log`); after the fix the file is **4/4 passed** (`w3/test-openapi-after-fix.log`). `w3/inventory-check-final.log` is **92 API routes / 0 drift** (frontend 23 unchanged), and `scripts/export_openapi.py --check` PASS. |
| Commit | **Not committed** — user prohibited commits; placeholder `TBD`. |

No other clear runtime or security defect was found. The following are residual
items, not patched:

- **ASK — AI practice cost bound:** `POST /practice/start` with `source=ai` is
  not per-user rate limited; only the documented translation drafts have a
  budget. Adding one is an architectural/product decision (new 429 contract and
  UI behavior), so it was not changed.
- **ASK — `docs/api-conventions.md:65-66`** still says “82 routes at HEAD
  `633fea3`”; the current baseline is `28c1784`. The count is still 82, so this
  is documentation-only drift in another workstream's document.
- **Accepted risk — root dev audit:** the two low advisories are in the pinned
  Mermaid/KaTeX documentation toolchain, not the frontend runtime; upgrading
  would change the pinned diagram tool and is outside this audit.
- **External limit — live model:** configured gateway returned 403 in prior
  rounds. This workstream deliberately spent no request; real-model quality is
  unverified.

## Commands and exact counts

All pytest commands were run from `backend/` with
`backend/.venv/Scripts/python.exe -m pytest ... -q`. Raw logs are under
`docs/qa/final-20261113/w3/`.

| Command / target | Result |
| --- | --- |
| `tests/test_ai_pipeline_purity.py tests/test_ai_prompt_hash.py tests/test_llm.py tests/test_login_throttle.py tests/test_rbac.py tests/dn/test_refresh_tokens.py tests/dn/test_openapi_contract.py` | **92 passed in 39.72s** |
| `tests/test_sandbox_safety.py tests/test_sandbox.py tests/dn/test_sandbox_protocol.py tests/dn/test_sandbox_connections.py` | **141 passed in 25.93s** |
| `tests/dn/test_ephemeral_sandbox.py` | **4 passed in 38.90s** |
| `tests/test_migrations.py tests/dn/test_database_initialization.py tests/dn/test_bank_contracts.py tests/test_bank_reconciliation.py` | **23 passed in 64.39s** |
| `tests/dn/test_practice_matrix.py tests/dn/test_practice_recovery.py tests/dn/test_practice_selection.py tests/dn/test_generation_auth_failures.py tests/dn/test_qa_provider.py` | **47 passed in 245.07s** |
| `tests/test_two_ai_pipeline.py tests/test_llm_release.py tests/test_llm.py tests/test_ai_pipeline_purity.py tests/test_ai_prompt_hash.py tests/test_ai_numeric_precision.py tests/test_real_provider_budget.py` | **166 passed in 23.94s** |
| `tests/test_auth.py tests/test_password_reset.py tests/test_login_throttle.py tests/test_rbac.py tests/test_role_management.py tests/test_shared_auth.py tests/test_release_auth.py tests/dn/test_refresh_tokens.py` | **98 passed in 61.31s** |
| `tests/dn/test_reviewed_postgres_semantics.py tests/dn/test_sql_contracts.py tests/test_sql_scoring.py tests/test_sql_release.py tests/test_localized_bank_sandbox.py` | **178 passed in 153.12s** |
| `tests/test_final_acceptance.py tests/test_result_contracts.py tests/test_supervisor_requirements.py tests/test_supervisor_completion.py tests/dn/test_openapi_contract.py` | **111 passed in 78.71s** |
| `tests/test_oauth.py tests/test_oauth_payloads.py tests/test_provisioning_contract.py` | **56 passed in 11.22s** |
| `tests/test_question_translation_draft.py tests/test_question_localization.py tests/test_draft_lifecycle.py` | **48 passed in 15.78s** |
| `tests/test_ai_admin.py tests/test_governed_generation.py tests/test_essay_grading.py tests/test_optional_essay.py` | **76 passed in 37.73s** |
| `tests/test_readiness.py tests/test_start_request_bindings.py tests/test_sessions.py` | **22 passed in 22.37s** |
| `tests/dn/test_environment_inventory.py tests/test_release_environment.py tests/test_bootstrap_admin.py` | **5 passed in 3.23s** |
| `tests/dn/test_practice_matrix.py -q -s` (explicit count) | **1 passed in 282.05s**; printed `actual_cases=2291100`, `failed=0`, `seconds=281.74` |
| `tests/dn/test_openapi_contract.py` after D1 fix | **4 passed in 1.14s** |
| New D1 test on baseline (before fix) | **1 failed** (expected; `inventory-response-model-before.log`) |

All final-state targeted invocations passed; the per-command counts above are
exact. Some files were intentionally rerun in isolation, so the table is not a
deduplicated unique-test count. No final-state test failed. One mistyped initial path
(`tests/test_question_translation.py`, not present) ran zero tests; the corrected
translation command above ran 48.

### Contract / inventory evidence

- Runtime: **82 paths / 92 operations**; committed `docs/openapi.json`:
  **82 / 92**; path sets identical; every operation and all **128** component
  schemas deep-equal.
- `scripts/export_openapi.py --check`: `OpenAPI matches the runtime contract`.
- `npm run inventory:check` (`w3/inventory-check-final.log`): **92 API routes,
  0 drift**; frontend inventory 23 routes unchanged.
- Status audit over all 92 operations: **0** decorator/OpenAPI 2xx mismatches.
- Response-model audit after D1: **92/92** inventory entries map to their 2xx
  schema (`list[...]`, unions, and refs included); **0** mismatches.
  `w3/inventory-response-model-check.log`.
- `tests/dn/test_openapi_contract.py`: every non-204 JSON 2xx has a schema;
  OAuth start/callback document 302 and no 200; login/complete document 401.

### Error envelope evidence

`w3/error-envelope-probe.log`:

| Request | Status / body |
| --- | --- |
| `GET /boom` (unhandled `RuntimeError` containing a DSN/secret marker) | 500 `{"error":{"code":"internal_error","message":"The request could not be completed..."}}` |
| `GET /bad` (`AppError(409)`) | 409 `{"error":{"code":"state_conflict",...}}` |
| `GET /missing` (`HTTPException(404)`) | 404 `{"error":{"code":"not_here",...}}` |
| `POST /validate` (invalid body containing a marker) | 422 `{"error":{"code":"validation_error",...}}` |

The probe asserted that none of `Traceback`, `SECRET-DSN`, `SECRET-VALUE`,
`postgresql://`, `File "` or `line ` appears in the response text.

### Security / AI evidence summary

- Refresh suite: 7/7; rotation hashes the token, replay revokes the family, the
  old and new access tokens are both rejected after replay, logout is idempotent.
- DB throttle: 10 concurrent failure inserts produce exactly 5 failures and 5
  `login_rate_limited` outcomes; key hashes never contain the email.
- Translation quota: two requests per admin per minute and twenty per hour are
  enforced with 429/`Retry-After`; disabled translation does not use grading
  credentials.
- SQL probe (`w3/sql-validator-probe.log`):

  | Input | Validator result |
  | --- | --- |
  | `SELECT 1; INSERT INTO t ...` / `SELECT 1; DROP TABLE t` | `multiple_statements` |
  | `UPDATE t SET a=1` / `CREATE TABLE x(a int)` / `SET search_path TO public` | `not_a_select` |
  | `SELECT set_config('search_path', ...)` | `unsafe_function` |
  | `SELECT * FROM pg_catalog.pg_authid` | `forbidden_schema` |
  | `SELECT * FROM t FOR UPDATE` / `SELECT * INTO backup FROM t` | `prohibited_statement` |
  | `COPY t TO '/tmp/x'` | `not_a_select` |
  | `WITH x AS (SELECT 1 AS n) SELECT * FROM x` | **ALLOWED** |

- Prompt/evaluator probe: one builder invocation, one evaluator invocation,
  byte-identical prompt, matching hash, two question comments.
- Terminal AI auth failure: exactly one provider call before bank/template
  recovery.
- Exact count: 2,291,100 exhaustive assembly cases, zero short/duplicate plans.

### Bank and migration evidence

- `python -m app.validate_bank`:
  `{"questions":5482,"types":{"mcq":2006,"sql":1747,"essay":1729},"invalid":0,
  "sql_execution":"not executed","failures":{}}`.
- `tests/test_migrations.py`: 8/8; fresh/pre-OAuth/post-OAuth/current schema
  matrix; second `apply_migrations()` returned `[]`; preserved account, concept,
  translation, attempt snapshots, grade evidence, and role audits.
- 19 migration files; no destructive migration added.

### Dependency audit

| Ecosystem | Command | Count |
| --- | --- | --- |
| Backend runtime | `pip-audit -r backend/requirements.txt` | 35 dependencies, **0 vulnerabilities** |
| Backend dev | `pip-audit -r backend/requirements-dev.txt` | 40 dependencies, **0 vulnerabilities** |
| Frontend | `npm audit --prefix frontend --json` | 285 dependencies (39 prod / 247 dev / 50 optional / 11 peer), **0 vulnerabilities** |
| Root tooling | `npm audit --json` | 206 dependencies, **2 low**, 0 moderate/high/critical (`@mermaid-js/mermaid-cli` → `katex`, dev-only) |
| Python health | `python -m pip check` | No broken requirements |

The root low advisories are in the pinned documentation/diagram toolchain, not
the shipped frontend bundle. The suggested `npm audit fix --force` would change
pinned tooling; not applied.

### Dead-code scan

`ruff check app --select F401,F811,F841,F821,F822,F823`: **27 findings** —
24 unused imports and 3 unused locals. The three locals are
`adaptive_engine.py:250` (`seq_no`), `grading_review.py:137`
(`manual_fallback`), and `practice_bank.py:68` (`known`). They have no observed
effect on behavior; **deferred/non-gating, no removal was made**. `ai/` passed
the same scan with zero findings. No duplicate prompt builder, evaluator, or
provider was found.

### Logs / secret hygiene

- `scripts/audit_secret_hygiene.py`: 5,535 reachable blobs plus tracked working
  files scanned; **0** history findings and **0** tracked findings; `pass=true`.
  The five ignored environment values were used only as scan needles and were
  never printed.
- W3 raw logs: 0 API-key/Bearer/password patterns.
- Log assertions cover Evaluator/Prompt Builder hashes only (never data),
  practice-generation diagnostics (shape/count/reason only), and timeout
  fallback (no provider message).

### Live key

- `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` are configured; only boolean
  presence was checked. The key value was not read into this report, printed,
  or passed to a live request by W3.
- **Real calls this workstream: 0.** The prior audited live ledger used **3/5**
  requests, all HTTP **403** before a completion; no retry or additional spend
  was made, and no retry is recommended. All AI behavior above is verified with
  fake providers/`httpx.MockTransport` or deterministic rules.

## Unfixed / unverified

1. AI practice generation has no per-user rate limit (ASK; see above).
2. Live model quality remains unverified because the configured gateway returned
   403 on all 3 prior ledgered attempts (3/5 used); the Evaluator/fallback
   contract is verified offline. Do not retry without owner authorization.
3. Root dev-only npm advisories remain (2 low); pinned toolchain left unchanged.
4. `docs/api-conventions.md` still names an older HEAD for the unchanged
   82-route count.
5. Not run: the full backend suite (~23 minutes), frontend unit/browser/E2E
   suites, documentation/Word/diagram gates, and any live model acceptance run.
   The targeted backend suites above cover the W3 scope; frontend audit/lint was
   run, but no frontend feature tests were run by W3.

## Changed files

Files changed by W3:

| File | Change |
| --- | --- |
| `scripts/generate_route_inventory.py` | Root fix: yield matched decorator; use its response model in both router and app-level branches. |
| `docs/inventory/api-routes.json` | Regenerated; only the three app-level `response_model` fields changed. |
| `backend/tests/dn/test_openapi_contract.py` | Added failing-before/passing-after regression for the three app-level response models. |
| `docs/qa/final-20261113/w3-backend-ai.md` | This report. |
| `docs/qa/final-20261113/w3/*` | Raw command logs and probes (new, untracked). |

No other file was modified by W3. `git status --short` also showed concurrent
workstream changes outside W3 (`README.md`, frontend components/config, brand
assets, `docs/qa/final-audit-20261113.md`, other QA folders); those were not
touched or staged.

Final `git status --short` snapshot (concurrent workstream files included):

```text
 M README.md
 M backend/tests/dn/test_openapi_contract.py
 M docs/inventory/api-routes.json
 M frontend/eslint.config.js
 M frontend/index.html
 M frontend/package.json
 D frontend/public/favicon.svg
 M frontend/src/components/AuthShell.jsx
 M frontend/src/components/Layout.jsx
 M frontend/src/i18n/en.json
 M frontend/src/i18n/vi.json
 M frontend/src/index.css
 M frontend/src/pages/ExamPage.jsx
 M frontend/src/pages/LandingPage.jsx
 M frontend/src/pages/LoginPage.jsx
 M scripts/generate_route_inventory.py
?? docs/qa/final-20261113/
?? docs/qa/final-audit-20261113.md
?? docs/qa/logo-20261113/
?? frontend/public/brand/
?? frontend/scripts/
?? frontend/src/components/BrandLogo.jsx
?? frontend/src/test/BrandAssets.test.jsx
```

## No-secret statement

No API key, password, JWT, database URL, SMTP value, or `.env` content appears
in this report or in the W3 raw logs. Only boolean configuration presence and
non-secret prompt hashes are recorded.
