# 03 — Options and Recommendation

## 1. Requirements

The design must:

1. allow a learner to submit a **script** of several statements;
2. allow DDL and DML (`CREATE TABLE`, `INSERT`, `UPDATE`, `DELETE`, limited
   `ALTER TABLE`, `DROP` of own objects);
3. keep the current SELECT-only behavior as the default and preserve every
   existing isolation guarantee;
4. never let learner SQL reach the application database, the host, another
   learner's schema, or the network;
5. always leave the sandbox clean, even after an error, timeout, or crash;
6. produce deterministic, explainable grading evidence;
7. be deployable in the current Compose/DN topology and testable in CI.

Non-goals: `COPY`/bulk import, stored procedures, triggers, extensions,
foreign data wrappers, user-defined types, and `VACUUM`/`ANALYZE` maintenance
commands.

## 2. Options

### Option A — Multi-statement SELECT only

Extend the validator to accept N read-only statements and execute them
sequentially; no DDL/DML.

- **Pros:** smallest change; no new role, no writable path; preserves the
  current threat model; can reuse the existing bounded-result code.
- **Cons:** does not meet the DDL/DML requirement; still needs a script runner
  and per-statement result UI.
- **Effort:** S (days).
- **Risk:** low.

### Option B — Shared sandbox + per-execution writable schema

Keep the long-lived `dbcas-sandbox` PostgreSQL. Add a `learner_rw` login role;
create a fresh `ds_<id>` schema per execution, owned by that role; allow
policy-checked DDL/DML inside it; always roll back; drop the schema.

- **Pros:** fastest (measured ~57 ms provision+execute+drop, `02-measurements.md`
  §3); no container lifecycle; works with the current Compose file and CI.
- **Cons:** all learners share one PostgreSQL process and one cluster. A
  privilege/validator bug is high impact; catalog side channels, lock waits,
  connection exhaustion, and disk/WAL pressure are shared; a crashed process
  can leave writable schemas behind; `cleanup_datasets` is not wired to
  startup (`01-current-state.md` G7).
- **Effort:** M (1–2 weeks).
- **Risk:** medium-high for untrusted DDL; acceptable for development only.

### Option C — Ephemeral container per dataset (recommended)

Reuse `EphemeralSandboxRunner`: one disposable PostgreSQL container per
dataset, `--network none`, read-only rootfs, tmpfs, UID 10001, cap-drop ALL,
no-new-privileges, 256 MB / 1 CPU / 128 PID, 45 s watchdog. Add a `learner_rw`
role and a per-dataset schema inside the container; run the script in one
transaction; always roll back; destroy the container.

- **Pros:** strongest containment; DDL/DML cannot outlive the attempt; no
  cross-learner state; natural cleanup even on process crash (watchdog + `--rm`);
  already implemented and exercised by Task 3.1.
- **Cons:** ~2.3–2.9 s per dataset (`02-measurements.md` §4); 2 concurrent
  slots per process; Docker socket is root-equivalent; the release Compose has
  no socket mount (`docker-compose.release.yml:42-56`); the executor image is
  899 MB.
- **Effort:** M–L (2–4 weeks, including grading and UI).
- **Risk:** medium (operational) but low for data isolation.

### Option D — Embedded engine (SQLite/DuckDB/WASM PostgreSQL)

Run learner SQL in-process or in a WASM sandbox.

- **Pros:** no Docker, fast, no shared database.
- **Cons:** PostgreSQL dialect and semantics differ; grading fidelity is poor
  for `RETURNING`, `ON CONFLICT`, `ALTER TABLE`, constraints, `search_path`,
  and error codes; a WASM PostgreSQL build is not a supported production
  dependency. This is a different product, not a sandbox hardening.
- **Effort:** L–XL.
- **Risk:** high (correctness).
- **Verdict:** rejected.

### Option E — Managed per-session database branches

Use a hosted PostgreSQL branch per attempt.

- **Pros:** strong isolation, no local Docker.
- **Cons:** external dependency, cost, latency, data residency, network
  egress, and an offline/local-development story that does not match the
  repository. Not viable for this project.
- **Verdict:** rejected.

## 3. Comparison

| Criterion | A: SELECT scripts | B: shared writable | C: ephemeral writable |
| --- | --- | --- | --- |
| Meets DDL/DML requirement | No | Yes | Yes |
| Isolation from other learners | Strong (read-only) | Medium (schema + role) | Strong (container) |
| Isolation from host/network | Strong | Strong (no network) | Strong (`--network none`) |
| Crash cleanup | Schema drop | Weak (stale `ds_*`) | Strong (watchdog + `--rm`) |
| Interactive latency | Low | **~57 ms** | **~2.3–2.9 s** |
| Submit grading latency | Low | Low | ~2.3–2.9 s per dataset |
| Deployment change | None | Role + grants | Socket/orchestrator + image |
| Blast radius of a policy bug | Read-only data | Shared cluster | One container |
| Effort | S | M | M–L |

## 4. Recommendation

**Adopt A now, C for writable exercises, and keep B for development only.**

1. **Default path (all environments):** multi-statement **read-only** scripts.
   This is Option A. It is a small, low-risk change that unlocks "setup +
   answer + check" scripts without any new privileges.
2. **Opt-in writable path (staging/production):** Option C. A question (or
   assessment) declares `sql_execution_mode = 'read_write'`; the server
   requires `SANDBOX_MODE=ephemeral` outside development and refuses to start
   otherwise. The script runs in a disposable container, in one transaction,
   and is always rolled back.
3. **Development fallback:** Option B behind an explicit
   `SQL_WRITABLE_SHARED_DEV=true` flag, never in staging/production. It keeps
   local iteration fast when Docker-in-Docker is inconvenient.
4. **Do not** make writable mode the default. Existing questions keep
   `read_only`; the migration default is `read_only`.

### Why not B for production?

The shared sandbox is a single PostgreSQL cluster shared by every learner.
Writable DDL/DML adds object creation, lock waits, WAL growth, and
catalog-visible state. The current `cleanup_datasets` is not called on startup,
and the deployment guard does not require ephemeral mode outside development
(`01-current-state.md` G7–G8). A single missed grant or parser bypass would be
cluster-wide. The measured 57 ms is attractive, but it buys speed by removing
the containment boundary that makes the feature safe.

### Why not C for every run?

The 2.3–2.9 s container cost is fine for submit-time grading and acceptable
for a "Run" button if the UI shows a spinner, but it is wasteful for the
existing SELECT-only exercises. Keeping the shared read-only path preserves
today's fast editor experience and avoids a needless Docker dependency for
schools that only use SELECT questions.

## 5. Decision record

| Decision | Choice | Reason |
| --- | --- | --- |
| Default mode | `read_only` | Backward compatible; no new privileges. |
| Writable production mode | `ephemeral` only | Container is the containment boundary. |
| Shared writable mode | development only, explicit flag | Fast local iteration; unacceptable blast radius elsewhere. |
| Transaction semantics | one transaction, always rollback | Atomic scripts; no persistence; easy cleanup. |
| Grading for DML/DDL | result first, `state` verifier second | Reuses existing comparator; state mode covers non-`RETURNING` writes. |
| New role | `learner_rw`, schema-scoped | Least privilege; no `CREATE` on `public`, no `TEMPORARY`. |
| Parser | AST allow-list, fail closed | Same approach as today, extended with statement kinds. |
| Rollout | feature flag + per-question opt-in | Can disable without a schema rollback. |
