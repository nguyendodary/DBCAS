# Bloat and inconsistency register

As of 2026-11-22, `develop2` `6421b5ad44a0eaaeb9be8d26068c8ca434ae5bb7`.
Classification: **SAFE-REMOVE** (no behaviour or data change), **KEEP**
(intentional or compatibility), **OWNER-DECISION** (migrations, v1/v2 data,
`docs/qa/**`, public behaviour, or a design/product choice).

This is an inventory, not permission to delete. Only SAFE-REMOVE items may be
fixed in Phase B; the rest are reported to the owner.

## SAFE-REMOVE

| # | Item | Evidence | Why safe |
| --- | --- | --- | --- |
| S1 | Demo runbook advertises a command that does not exist | `docs/demo/README.md:15-18` says `npm run demo:snapshot`; `package.json:6-25` has no such script. The feature lives only on the owner-skipped #89 branch (`git diff 6421b5a...origin/feat/demo-seed-snapshot -- package.json`). | Documentation-only; deleting the block makes the runbook true. The demo starts with the full seed (`backend/app/seed_demo.py:74-102`). |
| S2 | Root README points at a pre-merge branch that no longer exists | `README.md:14-15` says to switch to `integration/develop2-to-main-20261114` before PR #1 merges; `git branch -a` has no such branch, and `main` is separate. | Documentation-only; replace with the current `develop2` instruction. |
| S3 | `pytest` is a runtime dependency | `backend/requirements.txt:14`; used only by tests; `backend/requirements-dev.txt:1` already includes `requirements.txt`, so moving the pin keeps CI working. | No runtime import; the executor image also installs it unnecessarily (`sandbox/Dockerfile.ephemeral:1-13`). |
| S4 | Runbook's offline-provider Compose project is not the one `npm stop` controls | `docs/demo/README.md:68` uses `-p dbcas-demo`; `scripts/local.mjs:63,114-116` uses `dbcas-local` and only the local/demo compose files. | Documentation-only; align the project name and state that `npm start` must have created `.env` first. |

## KEEP

| # | Item | Evidence | Reason |
| --- | --- | --- | --- |
| K1 | `GRADING_STATE_MODE` flag is declared, default false, and never read | `backend/app/config.py:70`; the only other reference is `backend/tests/test_sql_multistatement.py:157`. | It records an unimplemented future capability; deleting it would hide the limitation. Document as future work. |
| K2 | `PROMPT_BUILDER_MODEL_PATH` / `PROMPT_BUILDER_TIMEOUT_SECONDS` are unused | `backend/app/config.py:177-179`; no runtime reference. | The comment explicitly says they are tolerated for environment compatibility; the builder is template-only (`docs/ai-pipeline.md:31-40`). |
| K3 | Broker B1 skeleton is present but not wired | `backend/app/services/broker/*`; `SANDBOX_BROKER=false` (`config.py:81`); only tests call the client. | Owner-approved default-off skeleton (#76); #80 is closed. Keep for the future broker work, never enable by default. |
| K4 | `concept_dependency` is created twice in `db/schema.sql` | First at `db/schema.sql:83-89`; migration-002 copy at `:440-446` with `IF NOT EXISTS`; FKs added at `:411-412`. | Harmless on fresh install (second create is a no-op, FKs are added by ALTER). It is schema history, not runtime bloat. Do not edit without owner approval. |
| K5 | `SystemSetting` model and `system_setting` table look unused | `backend/app/models.py:879` (retained import); read by `backend/app/services/corpus_seed.py:109,199`; `GET /admin/system` uses `system_settings.status`. | It is still a registry/settings source; not dead. |
| K6 | Large tracked frontend media (≈15.2 MB) | `docs/sql-sandbox/05-bloat-candidates.md:48-81`; assets under `frontend/src/assets`. | Real bloat, but changing media affects the approved UI and is a design choice. Owner decision, not a freeze fix. |
| K7 | Nine full-stack CI shards | `.github/workflows/dn-backend.yml:166-267`; measured 76.3 machine-minutes in `docs/sql-sandbox/05-bloat-candidates.md:83-96`. | Deliberate reliability coverage; changing it alters the required signal. Owner decision. |
| K8 | `GET /admin/questions?status=rejected` looks impossible | `backend/app/routers/admin.py:457` accepts it; `backend/app/services/question_service.py:253` maps it to `retired`, the stored value (`db/schema.sql:644`). | It is a working legacy alias, not a defect. Keep for client compatibility. |

## OWNER-DECISION

| # | Item | Evidence | Decision needed |
| --- | --- | --- | --- |
| O1 | Duplicate `concept_dependency` DDL in `db/schema.sql` | `db/schema.sql:83-89,411-412,440-446`. | Whether to consolidate the base DDL in a future migration; do not edit migrations for the freeze. |
| O2 | DB release-policy default is `IMMEDIATE`, API default is `HUMAN_VERIFIED` | `db/schema.sql:676-680` vs `backend/app/schemas.py:240`, `backend/app/repositories.py:490-503`. | Repository-created rows always pass a value; raw inserts differ. Changing the DB default is a migration. Document the difference. |
| O3 | Docs say all results are human-approved; FIXED TEST is AI-official | `README.md:84-88` and `docs/grading-and-sandbox.md:93-97` vs `assessment_lifecycle.py:233-238` and `result_version.py:180-278`. | Public behaviour/copy. The freeze PR corrects the documentation only; no code path changes. |
| O4 | Admin routes split across `admin.py` and `practice.py` | `/admin/system`, `/admin/accounts/{id}/reset-password`, `/admin/grading-reviews/{id}/run-sql` are in `backend/app/routers/practice.py:126-184`. | Organisational refactor; no behaviour change, but touching routes risks OpenAPI/inventory drift. Defer. |
| O5 | `docs/qa/**` generated facts and fixtures | `docs/qa/project-facts.json`, `docs/qa/**` are protected by AGENTS.md and read by `scripts/check_docs.py:7-10`. | Never edit. Any disagreement is reported, not fixed. |
| O6 | Old sample documents (outside the repo) | `Documents/Final/*.docx` cover 42 tables/routes from v1.2; current schema has 67 tables, 106 paths/118 operations. | Superseded by `docs/submission/*.docx`; keep the old files as history. |
| O7 | `pytest` image bloat in the executor and API | `docs/sql-sandbox/05-bloat-candidates.md:6-46`; `sandbox/Dockerfile.ephemeral:1-13`. | S3 is the minimal safe part; further image splitting needs an owner/ops change. |

## Totals

- SAFE-REMOVE: **4** (S1-S4).
- KEEP: **8** (K1-K8).
- OWNER-DECISION: **7** (O1-O7).
- No item proposes deleting a table, column, migration, v1/v2 result row, route,
  or any file under `docs/qa/**`.

## Phase B scope

Only S1-S4 are eligible for the freeze PR. S3 is a dependency move with the
test gate; S1, S2 and S4 are documentation corrections. Everything else is
reported as a known limitation or future work.
