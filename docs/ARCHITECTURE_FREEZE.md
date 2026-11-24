# Architecture Freeze — DBCAS

## 1. Baseline and scope

- Freeze date: 2026-11-24
- Branch: `develop2`
- Freeze commit: the T9 commit tagged `arch-freeze-v1` locally (tag not pushed). Resolve with `git rev-parse arch-freeze-v1`.
- Before T1: `436f82e` (integration baseline from `docs/PROJECT_AUDIT.md`)
- Accepted work: T1–T9, one commit each; see section 3.
- Production status: **HOLD**; no cloud deployment and no `develop2 -> main` PR in this freeze.

Architecture is unchanged in shape: FastAPI modular monolith (router → service →
repository → SQLAlchemy), PostgreSQL 17 via Docker Compose, React/Vite SPA behind
Nginx, SQL execution in disposable container(s). No new service, database, queue
technology or framework was introduced.

## 2. Frozen feature set

| # | Feature | Frozen behaviour | Evidence |
|---|---|---|---|
| F1 | Mode 1 (bank FIXED) | Reviewed bank; concept + one band; MCQ/SQL/essay mix; single-type caps 50/5/10; mixed caps 20/2/3, total 25; default 10/2/1 = 13; 30 minutes. | `backend/app/services/practice_config.py`, `frontend/src/assessmentStyle.js` |
| F2 | Mode 2 (AI adaptive) | `assessment_style=ADAPTIVE`, `source=ai`; one concept and one starting band; AI generates each next question in the UI language; correct = +1 level, wrong = −1 level clamped within band; prefetch for both next outcomes; timeout/failure/no key → reviewed bank fallback; no learner-visible error. | `backend/app/services/ai_adaptive.py`, `backend/app/services/practice_service.py` |
| F3 | AI question provenance | Snapshot stored on `attempt.question_snapshot` with `source` = `ai_generated` or `bank`; UI shows small `AI` badge; every served AI question is stored in `question_candidate` with concept, difficulty and `session_id` for existing admin validate/approve/reject. | `backend/app/services/ai_adaptive.py`, `frontend/src/pages/ExamPage.jsx`, `backend/app/routers/admin.py` |
| F4 | SQL sandbox | Default read-only SELECT, no network, statement timeout 3 s, row/byte limits, ephemeral container. Demo `writable` profile enables multi-statement DML/DDL, always rolled back. | `backend/app/services/sandbox_runner.py`, `docker-compose.demo-writable.yml`, `sandbox/init/00-learner-role.sh` |
| F5 | DML grading | Learner answer and trusted reference execute on the same dataset; final table state compared with stable row ordering (`sql_result.compare_state`). SELECT grading unchanged. DML fallback bank seeded with INSERT/UPDATE/DELETE and CREATE/ALTER/DROP-temp examples. | `backend/app/services/sql_grading.py`, `db/dml_practice_pack.json` |
| F6 | Grading/result release | MCQ deterministic; SQL semantic/state comparison; essay rubric + two-AI pipeline; FIXED TEST AI-official V1 at finalize; LEGACY human review; immutable result versions. | `backend/app/services/{grading_service,sql_grading,essay_grading,result_version,grading_review}.py` |
| F7 | i18n | `en`/`vi` UI copy; key sets identical (1689 keys in each after T8); technical identifiers preserved. | `frontend/src/i18n/{en,vi}.json`, `frontend/src/test/I18nParity.test.js` |
| F8 | Free/Pro demo | UI-only, enabled by default; plan persisted in `dbcas_demo_plan`; Free = Mode 1 + 5 sessions/day notice; Pro = Mode 2 + unlimited; no API/payment/migration. | `frontend/src/demo/freePro.jsx`, `frontend/src/pages/AssessmentsPage.jsx` |
| F9 | Auth/security | JWT access + rotating refresh, bcrypt, RBAC + role manager, OAuth optional, password-reset link via Mailpit; secret scanning and startup deployment guards. | `backend/app/{security,deps,config}.py`, `backend/app/services/{refresh_tokens,password_reset,oauth}.py` |
| F10 | Documents upload | Nginx accepts 30 MB HTTP bodies; backend accepts 20 MB binary (~27 MB base64 + JSON). | `deploy/nginx.conf`, `backend/tests/test_upload_limits.py` |

## 3. Accepted T1–T9 commits

| Task | Commit | Summary |
|---|---|---|
| T1 | `efb15e1` | Align Nginx upload limit with 20 MB API limit + regression test |
| T2 | `59a41df` | Remove hard-coded UI strings; en/vi key parity test |
| T3 | `39f1d36` | AI adaptive generation, validation, timeout, fallback, prefetch, source snapshot |
| T4 | `25ac1b3` | Record AI questions in `question_candidate`; admin approve/reject test |
| T5 | `2b0641a` | Adaptive supports MCQ/SQL/essay and mixed sequences within old caps |
| T6 | `ac74ed1` | Mode 1/2 UI, typed mix, small AI label |
| T7 | `3a16152` | Writable demo profile policy, DML state grading, DML fallback bank |
| T8 | `974b92b` | Free/Pro UI gating on by default with localStorage plan |
| T9 | `arch-freeze-v1` (tag on this commit) | Documentation sync, architecture freeze record, verification results |

## 4. Existing constraints (C1–C20, inherited unchanged)

| ID | Constraint | Source |
|---|---|---|
| C1 | Local Docker Compose only; no cloud; production HOLD. | `README.md`, `docs/agent/STATUS.md`, `docs/architecture/DECISIONS-FINAL.md` |
| C2 | PostgreSQL 17; schema via fresh DDL + additive migrations; no reset. | `db/schema.sql`, `backend/app/migrate.py` |
| C3 | Applied migrations must not be edited; checksums are enforced. | `backend/app/migrate.py:19-22` |
| C4 | Default learner SQL: SELECT-only, read-only transaction, 3 s timeout, 1000 rows/256 KiB, sandbox no network. | `backend/app/config.py`, `docker-compose.yml` |
| C5 | Writable SQL only with `SANDBOX_WRITABLE=true` + ephemeral mode; always rollback. | `backend/app/config.py`, `docker-compose.demo-writable.yml` |
| C6 | Ephemeral container: no network, read-only rootfs, uid/gid 10001, drop ALL caps, 256 MB/1 CPU/128 PIDs/45 s. | `ephemeral_sandbox.py`, `config.py` |
| C7 | API uses Docker CLI/socket; broker cutover is future work (#66 open). | `docker-compose.local.yml`, `docs/agent/STATUS.md` |
| C8 | Session 30 min; FIXED tab-leave grace 3 s, 3 violations cancel with zero. | `practice_service.py`, `config.py`, `fixed_paper.py` |
| C9 | Question caps: legacy 13; single 50/5/10; mixed 20/2/3 total 25; Mode 2 minimum 3. | `practice_config.py`, `practice_service.py` |
| C10 | Access JWT 60 min, absolute 480 min, refresh 7 days, HS256, password 8–72 bytes. | `config.py`, `schemas.py` |
| C11 | AI never required: no key/timeouts/failures fall back to deterministic rules or reviewed bank. | `evaluation_pipeline.py`, `ai_adaptive.py` |
| C12 | OpenRouter release requires official URL, concrete model, `deny` data collection, ZDR, pinned endpoint. | `config.py` |
| C13 | FIXED TEST = AI-official V1; LEGACY = human verification; no global release switch. | `result_version.py`, `grading_review.py`, `system_settings.py` |
| C14 | V1/V2 result rows immutable; score edits require audit reason. | `models.py`, `grading_review.py` |
| C15 | Synthetic demo data only; document upload requires explicit no-personal-data confirmation. | `README.md`, `schemas.py` |
| C16 | UI locales en/vi; 442 VI translations in the source bank; template questions are VI originals. | `i18n/index.js`, `db/question_translations_vi.json` |
| C17 | No `/sql-run` rate limit; per-execution limits + two-slot admission are the guard. | `docs/agent/STATUS.md` |
| C18 | Broker default OFF; B2 cutover, B3 writable broker, standalone broker service future. | `config.py`, `docs/analysis/broker-validation.md` |
| C19 | Free/Pro is UI-only; no backend route, payment or migration. | `frontend/src/demo/freePro.jsx` |
| C20 | One CI workflow, docs-only fast path, nine browser shards, three required checks. | `.github/workflows/dn-backend.yml` |

## 5. Accepted deviations from the pre-freeze audit (R1–R3 fixed)

| Audit item | Resolution | Evidence |
|---|---|---|
| R1 — stale root `README.txt` worktree/`.env` path | Corrected to `DBCAS\` as the only checkout and `DBCAS\.env` | `README.txt` |
| R2 — Nginx 1 MB vs backend 20 MB upload | Raised to 30 m; parity test added | `deploy/nginx.conf`, `backend/tests/test_upload_limits.py` |
| R3 — stale API/architecture docs | Route counts 106/118, removed removed admin-assessment routes, broker/snapshot/FREE-PRO status updated | `docs/api-conventions.md`, `docs/architecture/DECISIONS-FINAL.md` |

## 6. Known items deliberately left unchanged (accepted, not fixed)

The following audit findings remain in place by decision; they are not blockers for
this architecture freeze.

- R4 UI lacked AI source selector / count copy mismatch — resolved as a feature by T6; old docs updated in T9.
- R5 stale 5,482 bank figure — docs aligned to the current source count (`validate-bank`: 4046).
- R6 `db/seed.sql` uses `Admin123!` while demo seed uses `Demo12345!` — legacy stack, still present.
- R7 local Windows `format:check` CRLF issue — not fixed locally because CI checks out LF; project source files were formatted with Prettier.
- R8 `assessment_pool.py` unreferenced module — kept as historical residue.
- R9 i18n hardcoded strings — resolved by T2.
- R10 `system_settings.py` stale docstring — kept.
- R11 `project-facts.json` question-count values — protected file, not edited.
- R12 `docs/academic/README.md` v1.2 counts/copy — kept as dated revision.
- R13 duplicate `concept_dependency` DDL in base schema — owner decision O1, kept.
- R14 DB `IMMEDIATE` vs API `HUMAN_VERIFIED` default — owner decision O2, kept.
- R15 broker not wired to runtime — kept default OFF.
- R16 no SQL-run rate limit — kept with per-execution limits.
- R17 stale demo snapshot documentation — updated by T9 where relevant; old dated reports remain historical.
- R18 multiple document sets with different baselines — `docs/ARCHITECTURE_FREEZE.md` is now the freeze source of truth.
- R19 `scripts/README.md` lists a missing `ai.mjs` — kept.
- R20 two seed entry points — kept for the legacy Compose stack.

## 7. Verification performed for this freeze

All commands below were run on the freeze working tree before this document was
committed. Results are copied verbatim from the corresponding command output.

Logs for every gate are committed under [`freeze-logs/`](agent/freeze-logs/);
each result below refers to a file there.

| Gate | Command | Result | Log |
|---|---|---|---|
| Backend lint | `python -m ruff check app tests manage.py` | All checks passed! | [`backend-lint.log`](agent/freeze-logs/backend-lint.log) |
| Backend full test | `python -m pytest -q` (from `backend/`) | 1945 passed, 7 skipped (final run after the two post-freeze bug fixes; the earlier run that exposed the 5 failures is kept for evidence) | [`backend-pytest-final.log`](agent/freeze-logs/backend-pytest-final.log), [`backend-pytest-full.log`](agent/freeze-logs/backend-pytest-full.log), [`pytest-environment-limitation.log`](agent/freeze-logs/pytest-environment-limitation.log) |
| Frontend lint | `npm --prefix frontend run lint` | PASS (ESLint, `--max-warnings=0`) | [`frontend-lint.log`](agent/freeze-logs/frontend-lint.log) |
| Frontend unit | `npm --prefix frontend test -- --maxWorkers=2` | 54 files / 463 tests passed | [`frontend-test.log`](agent/freeze-logs/frontend-test.log) |
| Docs gate | `python scripts/check_docs.py` | PASS — 48 assertions; 106 API paths / 118 operations; schema, migrations, Compose, OpenAPI and frontend routes match | [`docs-check.log`](agent/freeze-logs/docs-check.log) |
| OpenAPI contract | `python scripts/export_openapi.py --check` | OpenAPI matches the runtime contract (106 paths) | [`openapi-check.log`](agent/freeze-logs/openapi-check.log) |
| Env inventory | `python scripts/check_environment.py` | 112 backend and 3 frontend keys documented; no values loaded | [`env-check.log`](agent/freeze-logs/env-check.log) |
| Launcher/manual smoke | `npm start` + browser flow | PASS — login, Pro demo, Mode 2 with MCQ/SQL/essay, submit, provisional evaluation page, admin login and empty candidate queue; AI provider rate-limited so bank fallback served every question | [`manual-flow.log`](agent/freeze-logs/manual-flow.log) |
| Fallback check | clear LLM keys, repeat Mode 2 | PASS — session 8 served a reviewed bank question with no error | [`fallback-check.log`](agent/freeze-logs/fallback-check.log) |

The original full backend run exposed one T9 regression (the shared validator
test used a read-only runner for the new DML fixtures); it was fixed and the
affected suites rerun green (44 passed). Four further failures were traced to
two independent defects and fixed after the freeze as owner-approved bug fixes,
each with its own commit (see 7.1). The final full run is completely green:
1945 passed, 7 skipped. No gate was weakened. The manual flow also showed the
configured OpenRouter free model returning HTTP 429 to structured prompts;
Mode 2 silently used the reviewed bank as designed, so the admin candidate queue
was empty and the approve path remains covered by the T4 test suite.

### 7.1 Post-freeze bug fixes (owner-approved, no architecture change)

- **Ephemeral executor** (`27c3e14`, log
  [`bug-a-ephemeral-exec.md`](agent/freeze-logs/bug-a-ephemeral-exec.md)): the
  native Windows Docker shim discarded every `docker exec` attach stream, and
  the trusted in-container job rejected its own writable Settings because
  `sandbox_mode` defaulted to `shared`. The Windows CLI now prefers WSL Docker
  when available; the job declares `sandbox_mode=ephemeral`. The missing shared
  sandbox role was identified as `learner_rw` and is now named in the error.
  All 5 ephemeral tests pass; a real UPDATE and DELETE each graded 5.00/5.00
  with the table state captured before rollback.
- **Grade visibility** (Bug B, log
  [`bug-b-grade-visibility.md`](agent/freeze-logs/bug-b-grade-visibility.md)):
  `is_correct` is null in submit responses because HUMAN_VERIFIED hides scores
  until publication, not because grading failed. A controlled E2E with known
  answer keys showed ability 1→2 (correct), 2→1 (wrong), 1→2 (correct) and
  persisted scores `[1.00, 0.00, 1.00]`; a regression test documents it. No
  production change was needed.

## 8. Architecture freeze conclusion

**Có, sau khi xử lý 3 mục blocking (R1–R3), đã được chấp nhận trong T1/T2/T9.**
Không thêm tính năng, công nghệ, dependency hay ràng buộc mới sau commit được
gắn tag `arch-freeze-v1`. Mọi thay đổi sau freeze chỉ được chấp nhận khi là sửa lỗi,
lỗi bảo mật, hoặc có owner duyệt kèm cập nhật tài liệu này.
