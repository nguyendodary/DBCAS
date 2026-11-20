# 06 — Delivery Plan, Tests, Rollback, and Risks

This is a proposed plan only. No implementation is part of this branch.

## 1. Phases

### Phase 0 — Sign-off (no code)

1. Owner confirms the product need for writable DDL/DML exercises and the
   grading semantics (`07-unknowns.md` U1–U5).
2. Security owner reviews the policy matrix in `04-target-design.md` §4.
3. Ops owner confirms where ephemeral containers can run in staging/production
   (Docker socket, sidecar, or orchestrator) — U6.
4. Baseline measurements in `02-measurements.md` are accepted as local
   synthetic evidence, not production SLAs.

Exit criteria: a written decision record for mode defaults and grading mode.

### Phase 1 — Multi-statement read-only scripts (no new privileges)

Scope:

- `sqlglot.parse` for all statements; policy for N read-only statements.
- `execute_script` with per-statement results and the existing bounded row/byte
  wrappers.
- `SqlRunResult.statements` (additive) and editor "Messages" tab.
- Startup `cleanup_datasets()` call for shared mode.
- Tests from §2 (read-only subset).

Safety properties:

- `learner_ro`, role grants, and read-only transaction unchanged.
- No DDL/DML allowed; no new role.
- `max_statements=32`, script budget 5 s, row/byte caps unchanged.

Estimated effort: 3–5 days. Risk: low.

### Phase 2 — Writable scripts in ephemeral containers (staging only)

Scope:

- `learner_rw` role and per-execution schema owned by that role.
- Setup executed as `learner_rw`; schema dropped/container destroyed after
  rollback.
- Statement policy from `04-target-design.md` §4.
- `question.sql_execution_mode`, `sql_test_dataset.grading_mode`,
  `verifier_sql` (migration 029).
- `result` and `state` grading modes; `sql_features` DML/DDL keys.
- `SQL_WRITABLE_ENABLED` flag and startup refusal for shared mode outside
  development.
- 512 MB / 256 PID / 60 s lifetime for writable containers; measure and tune.
- Full test matrix from §2.

Exit criteria: staging canary, no policy-bypass findings, p95 grading latency
within the agreed budget, cleanup verified after crash/timeout/OOM.

Estimated effort: 2–4 weeks. Risk: medium.

### Phase 3 — Production canary

- Enable `SQL_WRITABLE_ENABLED=true` for a small set of non-high-stakes
  courses/questions only.
- Keep `read_only` default for everything else.
- Monitor metrics and alerts from `04-target-design.md` §11 for at least one
  full assessment cycle.
- Review audit log and any `WARN` policy violations before widening.

Production remains **HOLD** until this phase is explicitly approved.

### Phase 4 — Hardening and cost work

- Warm container pool / per-attempt container reuse to cut the 2.3–2.9 s
  ephemeral cost.
- Seed template/snapshot to cut the 144 s cold seed.
- Executor image slimming and removal of `pytest` from runtime requirements.
- CI matrix reduction on pull requests.
- Wire `cleanup_datasets()` and stale-lease sweeps for shared dev mode.
- Decide whether `script` grading mode is worth keeping.

## 2. Test plan

### 2.1 Static policy (unit, table-driven)

For every statement kind in `04-target-design.md` §4: allowed form, rejected
variant, and expected `error_type`. Include:

- `INSERT`/`UPDATE`/`DELETE`/`CREATE`/`ALTER`/`DROP`/`TRUNCATE`;
- `WITH ... INSERT/UPDATE/DELETE` (data-modifying CTEs) — reject in v1;
- `SELECT INTO`, `FOR UPDATE`, `MERGE`;
- schema-qualified forms: own schema allowed, `public`, `pg_catalog`,
  `information_schema`, `pg_temp`, other `ds_*`, and cross-database qualifiers
  rejected;
- quoted identifiers, mixed case, Unicode, comments, `;` inside string
  literals, dollar quoting, NUL/control characters, oversized input;
- functions: existing deny-list, all `pg_*`, `dblink*`, `lo_*`, `xml_*`,
  `nextval`, `setval`, `set_config`, `current_setting`, `pg_sleep`;
- multi-statement split, empty statements, 33+ statements, parse errors;
- `CREATE TABLE ... AS SELECT`, `INSERT ... SELECT`, `LIKE`, `REFERENCES`,
  `CHECK`, `DEFAULT`, generated columns, sequences, indexes, `ALTER TABLE`
  subcommands.

### 2.2 Privilege and isolation integration

- `CREATE TABLE public.x` → denied by policy and by role.
- `CREATE SCHEMA`, `CREATE EXTENSION`, `CREATE FUNCTION`, `CREATE ROLE`,
  `ALTER ROLE`, `GRANT`, `REVOKE`, `SET ROLE`, `SET`, `RESET`, `DISCARD`, `LOAD`,
  `COPY`, `DO`, `CALL`, `EXECUTE`, `PREPARE`, `DECLARE`, `LOCK`, `LISTEN`,
  `NOTIFY`, `VACUUM`, `ANALYZE`, `REINDEX`, `CLUSTER`, `CHECKPOINT`, `COMMENT`,
  `SECURITY LABEL`, `REFRESH MATERIALIZED VIEW` → denied.
- `pg_read_file`, `pg_ls_dir`, `pg_stat_file`, `lo_import`, `lo_export`,
  `dblink`, `pg_terminate_backend`, `pg_sleep` → denied.
- `SELECT * FROM pg_catalog.pg_class`, `information_schema.tables`, another
  learner's `ds_*` schema → denied.
- Temporary tables → denied.
- `ALTER TABLE <fixture> OWNER TO ...`, `SET SCHEMA`, `SET TABLESPACE` → denied.
- Verify `has_schema_privilege('learner_rw','public','CREATE') = false`,
  `has_database_privilege(...,'CREATE') = false`, `rolsuper=false`,
  `rolcreatedb=false`, `rolcreaterole=false`, `rolbypassrls=false`.
- Two learners with the same table names in different schemas → no
  interference; catalog checks cannot see the other schema.

### 2.3 Resource / DoS

- 10,000-row `INSERT` within limits; 100,000-row `INSERT` aborts by
  `max_dml_rows`.
- `generate_series(1, 1e9)`, recursive CTE without a bound, Cartesian join →
  `timeout` or `out_of_memory`, script rolled back.
- 32 statements each near the 3 s timeout → script budget enforced.
- 64+ objects → rejected.
- Disk/temp-file exhaustion → `disk_full`, no container leak.
- Concurrent runs beyond capacity → `sandbox_busy` 503, then recovery.
- Kill the API process mid-script → ephemeral watchdog removes the container;
  shared-mode startup sweep removes stale `ds_*` schemas.

### 2.4 Grading

- `result` mode: `SELECT`, `INSERT ... RETURNING`, `UPDATE ... RETURNING`.
- `state` mode: verifier sees uncommitted rows; `INSERT`/`UPDATE`/`DELETE`
  without `RETURNING`; `ALTER TABLE` catalog checks.
- `script` mode: command tags and row counts.
- Edge datasets; required-concept checks including new DML/DDL keys.
- Verifier is SELECT-only and cannot write.
- Error on statement 2 rolls back statement 1; dataset marked `error`, not
  silently passed.
- Expected-result leakage: `expected_result` and `setup_sql` never appear in
  `attempt.grading_detail` or the API response.

### 2.5 Ephemeral container

- `docker inspect`: `--network none`, read-only rootfs, tmpfs mounts, UID
  10001, cap-drop ALL, no-new-privileges, 256/512 MB, 1 CPU, 128/256 PID.
- Image label `com.dbcas.sandbox-protocol=1`.
- No published port; only `docker exec` transport.
- Cleanup on success, policy error, timeout, OOM, host-process death, and
  watchdog expiry.
- Ownership check refuses to remove a container not labeled with the current
  executor owner (`ephemeral_sandbox.py:68-81`).

### 2.6 End-to-end / CI

- Exam page and fixed-paper runner: run a 3-statement script, see per-statement
  messages and last result.
- Submit a writable question; score and evidence correct.
- Backend unit/integration tests in `dn-backend.yml` `backend` job.
- Playwright specs in the e2e shards; QA/smoke unchanged.
- Docs-only PR: confirm the matrix is skipped and `frontend-local` passes with
  the docs-only message (this PR's actual result is reported in the PR).

### 2.7 Adversarial review

- Fuzz the validator with sqlglot-generated mutations.
- Review with a second engineer before enabling production canary.
- Attempt parser-bypass classes from `04-target-design.md` §4.2 explicitly.

## 3. Rollout

1. Merge migration 029 separately from feature enablement (additive only).
2. Deploy with `SQL_WRITABLE_ENABLED=false`; verify no behavior change.
3. Enable for one staging question; run the full test matrix.
4. Enable for a staging cohort; monitor for one assessment cycle.
5. Production canary with explicit owner approval; production otherwise HOLD.

## 4. Rollback

Immediate (no code deploy):

1. Set `SQL_WRITABLE_ENABLED=false` and restart/reload the API. Writable
   questions return `422 sql_mode_disabled`; read-only path is unaffected.
2. If an ephemeral container is stuck, its 45 s watchdog and `--rm` will
   remove it; `docker ps --filter label=com.dbcas.ephemeral` can confirm.
3. If shared-mode schemas leaked, run `runner.cleanup_datasets()` (wire a
   management command or use the existing method directly).
4. Keep `question.sql_execution_mode` values in the DB; they are inert while
   the flag is off.

Full rollback:

1. Deploy the previous image.
2. Leave migration 029 in place (additive columns with safe defaults); do not
   drop columns while old code might still read them.
3. Revert the feature flag and Compose changes if any.
4. Confirm `learner_ro` role/grants unchanged; `learner_rw` can remain but has
   no grants to anything outside disposable schemas.

No learner data is written to the app DB in either path, so rollback needs no
data repair.

## 5. Risk register

| ID | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R1 | Parser bypass allows an out-of-schema object | Low | High | Role privileges as second gate; deny `public`/catalog; adversarial tests. |
| R2 | DDL/DML leaks state between learners | Low | High | Schema per execution; ephemeral mode outside dev; ownership checks. |
| R3 | Resource exhaustion (CPU/memory/disk) | Medium | Medium | Statement/script budgets, row/byte/object caps, container limits, OOM alerts. |
| R4 | Grading can be gamed by faking state | Medium | Medium | `relkind`/column checks, catalog checks, review-recommended flag. |
| R5 | Ephemeral latency hurts UX | High | Low | Spinner, async submit, warm pool in Phase 4. |
| R6 | Stale schemas/containers after crash | Medium | Medium | Watchdog, `--rm`, startup sweep, cleanup metrics. |
| R7 | Release stack cannot run ephemeral mode | High | Medium | Owner decision on socket/sidecar before Phase 2; startup refusal. |
| R8 | `pg_*` function denials break learner answers | Medium | Low | Document trade-off; allow a reviewed safe subset later. |
| R9 | New role provisioning fails on existing volumes | Medium | Medium | Idempotent role creation; readiness check; manual runbook. |
| R10 | CI cost grows with new tests | High | Low | Add tests to existing `backend` job first; shard only if needed. |

## 6. Definition of done

- All tests in §2 pass on `develop2` CI.
- Threat-model review signed off (Phase 0 record).
- No app DB connection is used by writable execution (verified in code review
  and tests).
- Cleanup verified after success, error, timeout, OOM, and process kill.
- Metrics and alerts deployed before production canary.
- Production HOLD is lifted only by explicit owner decision.
