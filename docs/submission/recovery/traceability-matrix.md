# Content traceability matrix — documentation claim → implementation evidence

Condensed from `implementation-audit.md` (full evidence and file paths there).
Status is after the 2026-11-25 revision.

| Area | Documentation claim | Implementation evidence | Status | Action taken |
|---|---|---|---|---|
| Architecture | 7 registered routers / 72 top-level service modules | `backend/app/main.py:15,69-75`; `backend/app/services/` | Outdated → Verified | Corrected in Architecture §1.2, Code Standards §2, SOURCE_CODE.md; convention stated |
| Architecture | 106 paths / 118 operations | `docs/openapi.json`; `scripts/export_openapi.py --check` | Verified | Keep |
| Architecture | Four-tier modular monolith, ephemeral SQL executor | `backend/app/`, `sandbox/`, `docker-compose.local.yml` | Verified | Keep |
| Database | 67 tables / 561 columns / 122 FKs / 159 indexes / 28 migrations | `docs/diagrams/schema-028/schema-introspection.json` (PG 17.12), `db/migrations/*.sql` | Verified | Keep; add 68-DDL/67-distinct nuance as owner note |
| Database | 68 PK + 41 unique + 51 standalone indexes | Same introspection, classified by definition: 67 / 50 / 42 | Outdated → Verified | Corrected in Database §6; sum now 159 |
| Database | 4 legacy `assessment*` tables; `assessment_session` live | `manifest.json:518-523`; `scripts/check_docs.py:156-164` | Verified | Keep |
| API | 12 auth paths, 101 role-protected operations, OAuth + reset | `backend/app/routers/{auth,oauth}.py`, `deps.py`, `openapi.py` | Verified | Keep |
| Workflow | TEST vs PRACTICE purpose, V1 publication, 7-day review window | `db/migrations/025_session_purpose.sql`; `result_version.py`, `grading_review.py` | Verified | Publication wording corrected in Proposal §5 |
| Workflow | Mode 1 bank / Mode 2 AI; prompt builder + evaluator; fallback | `practice_service.py`, `ai_adaptive.py`, `prompt_builder.py`, `evaluation_pipeline.py` | Verified | Keep |
| Workflow | Free/Pro UI-only demo, 5 sessions/day | `frontend/src/demo/freePro.jsx`; flag `VITE_DEMO_FREE_PRO` | Verified (client-side only) | Keep; note stale E2E string in `document-index.md` open issues |
| Validation | Pydantic models, uniform error envelope, AST-based SQL policy | `backend/app/schemas.py`, `errors.py`, `sql_validator.py` | Verified | Keep |
| CI/CD | 14 of 14 jobs successful | `final-ci-conclusion.log` at `d6df804`, run 45597486074 | Verified for that commit only | Commit attribution added to Technical Report, SOURCE_CODE.md, doc-verify.md |
| CI/CD | `docs:check`, `docs:verify-word`, `inventory:check`, `secrets:scan` | `package.json:6-29` | Verified; re-run here | Keep; outputs in `technical-verification-report.md` |
| Testing | 1,940 passed / 7 skipped, 0:23:54 | `backend-pytest-final.log:35` | Verified | Duration corrected (was "24 min 22 s") |
| Testing | 54 vitest files / 463 tests; 25+3 browser specs; 152 browser tests passed | `frontend-test.log`, shard logs, directory enumeration | Verified | "4 skipped" removed; spec convention stated |
| Testing | Secret scan 0 findings | `final-secrets-tree.log:5` (3,083 files) | Verified | "3,129 files" corrected; unsupported commit count removed |
| Testing | 186 contrast pairs, 0 failures | `final-ui-contrast.log` | Verified | Log citation added |
| Security | Sandbox flags default OFF, broker stub behind default-OFF flag, production HOLD | `backend/app/config.py:42-109`; `STATUS.md` | Verified | Keep |
| Figures | Recreated Gantt is FITAI-styled and legible | `assets/gantt-roadmap.svg` + rendered page 15, visually inspected | Verified | Source retained |

Unverifiable claims that were removed rather than guessed: pytest "24 min 22 s",
browser "4 skipped", secret scan "3,129 files"/"1,042 commits", backend/frontend
line counts presented as exact without a saved log.
