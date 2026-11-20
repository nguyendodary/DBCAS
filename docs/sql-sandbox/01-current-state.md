# 01 — Current State Audit

Baseline: `origin/develop2` at `955abd075928bc3c3d738a20cd942dfc7bb256c8`.

## 1. Request path

The browser sends learner SQL to one endpoint:

- `frontend/src/pages/ExamPage.jsx:364-380` — `runSql()` posts to
  `POST /sessions/{sessionId}/sql-run` with `{ question_id, sql }`.
- `frontend/src/pages/FixedPaperRunner.jsx:397-410` — the same call in the
  fixed-paper runner.
- `backend/app/routers/sessions.py:301-311` — routes the request to
  `sql_service.run_learner_sql`.
- `backend/app/services/sql_service.py:47-56` — provisions the question's
  primary (non-edge) dataset, executes the learner SQL, and drops the dataset
  schema in `finally`.
- `backend/app/schemas.py:503-520` — `RunSqlRequest` carries `question_id` and
  `sql` (max 16,000 characters); `SqlRunResult` carries `success`, `columns`,
  `column_types`, `rows`, `row_count`, `execution_time_ms`, and a sanitized
  `error_type` / `error_message`.

The frontend has **no SQL policy**. `frontend/src/components/SqlEditor.jsx:5`
includes `insert`, `update`, `delete`, `create`, `alter`, and `drop` in its
keyword list, and the editor placeholder is `SELECT ...`
(`SqlEditor.jsx:93`). The UI therefore hints at DML/DDL that the backend
currently rejects. This is a UX inconsistency, not a security boundary: the
server is authoritative.

## 2. Parser / policy layer

`backend/app/services/sql_validator.py` is the static gate.

| Control | Evidence | Behavior |
| --- | --- | --- |
| Allowed roots | `sql_validator.py:23-30` | `Select`, `Union`, `Intersect`, `Except`, `Subquery`, `Values` only. |
| Forbidden nodes | `sql_validator.py:34-57` | `Insert`, `Update`, `Delete`, `Merge`, `Drop`, `Alter`, `Create`, `TruncateTable`, `Command` (EXPLAIN/COPY/VACUUM/CALL/DO/GRANT/SET/…), `Transaction`, `Set`, `Copy`, `Pragma`, `Describe`, `Analyze`, `Cache`, `Uncache`, `Grant`, `Revoke`, `Into`, `Lock`, `UserDefinedFunction`. |
| Forbidden schemas | `sql_validator.py:61` | `pg_catalog`, `pg_toast`, `information_schema`; any `pg_*` schema. |
| Forbidden names | `sql_validator.py:65` | Unqualified names starting `pg_` or `sql_`. |
| Unsafe functions | `sql_validator.py:70-109` | Deny-list plus `pg_*`, `dblink*`, `lo_*`, `xml_*`, etc. |
| Single statement | `sql_validator.py:147-148` | More than one parsed statement returns `multiple_statements`. |
| Root check | `sql_validator.py:150-155` | Anything else returns `not_a_select` with "Only a single read-only SELECT query is allowed in the sandbox". |
| Schema qualifiers | `sql_validator.py:157-178` | `public` is always allowed in addition to the provisioned dataset schema. |
| Function check | `sql_validator.py:179-192` | Rejects the deny-list and unsafe prefixes. |

Observed behavior at the baseline (run against the local backend virtualenv):

```text
select:        None
insert:        ('not_a_select', 'Only a single read-only SELECT query is allowed in the sandbox')
create:        ('not_a_select', 'Only a single read-only SELECT query is allowed in the sandbox')
update:        ('not_a_select', 'Only a single read-only SELECT query is allowed in the sandbox')
multi_select:  ('multiple_statements', 'Only a single SELECT statement is allowed')
cte_insert:    ('not_a_select', 'Only a single read-only SELECT query is allowed in the sandbox')
select_into:   ('prohibited_statement', 'into constructs are not allowed in learner queries')
copy:          ('not_a_select', 'Only a single read-only SELECT query is allowed in the sandbox')
do:            ('not_a_select', 'Only a single read-only SELECT query is allowed in the sandbox')
set_role:      ('not_a_select', 'Only a single read-only SELECT query is allowed in the sandbox')
drop:          ('not_a_select', 'Only a single read-only SELECT query is allowed in the sandbox')
```

**Gap:** the policy is a `SELECT`-only allow-list, not a writable-statement
policy. It also cannot parse a script: `sqlglot.parse` splits statements, but
the validator rejects anything with more than one.

## 3. Shared sandbox runner

`backend/app/services/sandbox_runner.py` executes the validated statement.

- `:164-188` — re-validates, rejects empty/oversized SQL, passes the dataset
  schema as the only extra allowed schema.
- `:190-194` — opens a new psycopg connection per execution (`autocommit=True`).
  There is no connection pool.
- `:205-209` — sets `SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`,
  `statement_timeout`, and `idle_in_transaction_session_timeout`.
- `:210-215` — sets `search_path` to the provisioned `ds_*` schema.
- `:216` — `BEGIN`.
- `:219-222` — parses the SQL again and uses a named cursor's `DESCRIBE` to get
  the result shape.
- `:235` — wraps the statement in `SELECT ... FROM (<canonical>) AS _r(...)`
  with `LIMIT max_rows + 1`, plus per-cell and total-byte guards.
- `:251` — always `ROLLBACK`.
- `:280-322` — `provision_dataset`: validates setup SQL, creates
  `ds_<12 hex>` with `AUTHORIZATION dbcas_dataset_setup`, switches to that
  non-login role, grants `USAGE` and default `SELECT` to `learner_ro`, then runs
  the validated setup statements.
- `:324-362` — `drop_dataset` and `cleanup_datasets`; `cleanup_datasets` is
  defined but **not called from application startup** (only the definition was
  found by repository search).
- `:377+` — `validate_environment` checks the learner role, timeout, and
  read-only default.

**Consequences for DDL/DML:**

1. `learner_ro` has no `CREATE`, `INSERT`, `UPDATE`, or `DELETE` privilege
   (`sandbox/init/00-learner-role.sh:19-28`), so DDL/DML would fail with
   `42501` even if the parser allowed it.
2. The `DESCRIBE` + bounded-subquery wrapper assumes a row-returning `SELECT`.
   A DDL or DML statement cannot be embedded in `FROM (...)`.
3. The statement is effectively executed twice for `SELECT` (once for shape,
   once for the bounded query). For DML that would duplicate writes; the
   wrapper must be replaced, not extended.
4. Always-rollback is correct for editor runs, but grading a DDL/DML exercise
   needs a verifier to read the uncommitted state **before** rollback.

## 4. Ephemeral sandbox runner

`backend/app/services/ephemeral_sandbox.py` is the stronger isolation mode.

- `:18` — at most two concurrent ephemeral containers per process
  (`threading.BoundedSemaphore(2)`).
- `:83-114` — creates one disposable container per dataset:
  `--network none`, `--memory 256m`, `--memory-swap 256m`, `--cpus 1`,
  `--pids-limit 128`, `--read-only`, `--user 10001:10001`, `--cap-drop ALL`,
  `--security-opt no-new-privileges`, tmpfs for data/run/tmp, random
  `POSTGRES_PASSWORD` and `SANDBOX_LEARNER_PASSWORD`, and a 45-second watchdog.
- `:116-133` — sends one JSON operation over stdin to
  `python -m app.sandbox_job` inside the container.
- `:135-168` — `provision_dataset` creates the container and lease;
  `execute` validates and calls the same `SandboxRunner` inside the container;
  `drop_dataset` removes the container.
- `:170-174` — `cleanup_datasets` drops every live lease.
- `backend/app/sandbox_job.py:10-33` — the in-container bridge constructs a
  `SandboxRunner` with unix-socket URLs and `deployment_mode="development"`,
  then dispatches `provision`, `execute`, or `validate`.

**Consequences:** ephemeral mode already gives the strongest containment and
natural cleanup, but it inherits the same SELECT-only validator and the same
single-statement execution model. It also costs a container start per dataset
(see `02-measurements.md`).

## 5. Database role and grants

`sandbox/init/00-learner-role.sh:19-28` creates the shared sandbox role:

```sql
CREATE ROLE learner_ro LOGIN PASSWORD :'learner_password';
ALTER ROLE learner_ro SET statement_timeout = :'statement_timeout';
ALTER ROLE learner_ro SET default_transaction_read_only = on;
ALTER ROLE learner_ro SET idle_in_transaction_session_timeout = '15s';
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE TEMPORARY ON DATABASE :"database_name" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"database_name" TO learner_ro;
GRANT USAGE ON SCHEMA public TO learner_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO learner_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO learner_ro;
```

Local verification (`docker exec dbcas-sandbox psql …`) confirmed
`learner_ro` is a non-superuser login with
`{statement_timeout=3000, default_transaction_read_only=on,
idle_in_transaction_session_timeout=15s}`, no `CREATE` on `public`, and
`USAGE` on `public`.

**Gap:** there is no writable role. A writable design needs a separate role
with `default_transaction_read_only=off`, no `CREATE` on `public`, no
`TEMPORARY`, and privileges only on a per-execution schema.

## 6. Dataset setup policy

`backend/app/services/dataset_setup.py:10-57` validates admin-authored setup
SQL before it reaches the provisioning connection:

- at most 64 statements, at most 64 KiB;
- only explicit `CREATE TABLE` (no `AS SELECT`), safe `CREATE VIEW` over
  read-only `SELECT`, and literal `INSERT ... VALUES`;
- unqualified local identifiers only;
- no functions, subqueries, storage properties, `REPLACE`, or references to
  undeclared tables.

This is a good model for the writable path: **the fixture is trusted and
bounded; the learner script is untrusted and policy-checked**.

## 7. Grading

`backend/app/services/sql_grading.py`:

- `:33-67` — for each dataset, provision the schema, execute the learner SQL,
  compare the returned columns/rows to `expected_result`, drop the schema.
- `:54-59` — an execution error fails only that dataset; a sandbox outage
  raises `sandbox_unavailable` so the answer is not scored.
- `:70-118` — score = `points * passed / total`; a missing required concept
  zeroes the score; evidence is stored in `attempt.grading_detail`.

`backend/app/services/sql_result.py` compares result sets as multisets, and
`backend/app/services/sql_features.py:21-48` maps required concepts to AST
features (`join`, `group_by`, `cte`, `window`, etc.).

**Gap:** grading assumes a row-returning final result. There is no way to grade
the *state* left by `INSERT`/`UPDATE`/`DELETE`/`ALTER`, and
`sql_features.py` has no DML/DDL feature keys.

## 8. Configuration and deployment

`backend/app/config.py`:

- `:49-58` — sandbox limits: 3,000 ms statement timeout, 1,000 rows, 16,000
  SQL bytes, 256 KiB result, 16 KiB cell, 64 KiB setup, 5 s connect timeout,
  `sandbox_mode` `shared` by default, 45 s container lifetime.
- `:141-145` — app DB pool 10 + 20 overflow, 5 s connect/pool timeouts.
- `:196-230` — staging/production safety: distinct sandbox and app DB
  host/port (`:220-221`), non-demo passwords, HTTPS, statement timeout ≤ 3,000
  ms.
- **No guard requires `sandbox_mode=ephemeral` outside development.** A
  staging/production deployment can run `shared` today.

Compose facts:

- `docker-compose.yml:1-13` — separate `db-net` and `sandbox-net`, IP
  masquerade disabled; `:45-60` — shared sandbox built from `sandbox/`, 256 MB,
  200 PIDs, `no-new-privileges`, published port.
- `docker-compose.local.yml:26-30` — builds `dbcas-sql-ephemeral:local` as an
  image-only service; `:38` sets `SANDBOX_MODE=ephemeral`; `:71-72` seeds via
  `app.seed_demo`; `:84` mounts the Docker socket into the app.
- `docker-compose.dn.yml:17-26` — still starts a shared `sandbox` service even
  though `:50` sets `SANDBOX_MODE=ephemeral`; `:67-71` also builds the
  ephemeral image. The shared service is redundant in ephemeral mode.
- `docker-compose.release.yml:20-31` — release stack starts a shared sandbox;
  `:42-56` backend has **no Docker socket mount**, so `SANDBOX_MODE=ephemeral`
  cannot work in this stack as written.
- `backend/Dockerfile:1-14` — API image copies the 44 MB Docker CLI binary and
  runs two uvicorn workers.
- `sandbox/Dockerfile.ephemeral:1-13` — `postgres:17` + Python venv + full
  `backend/requirements.txt` + app source; labeled
  `com.dbcas.sandbox-protocol=1`.

## 9. CI behavior for a docs-only PR

`.github/workflows/dn-backend.yml:15-46` sets `docs_only=true` when every
changed file is under `docs/*` or `standards/*`, **except** `docs/qa/*`.
The `secrets` and `backend` jobs still start, but their test steps are gated
on `docs_only != 'true'` (`:56-59`, `:79-118`) and are replaced with a
"docs-only PR" echo (`:60-61`, `:119-120`). `frontend-static` and
`frontend-shard` are skipped at the job level (`:124`, `:168`). `frontend-local`
is the fan-in aggregator and passes with a docs-only message. The exact run is
reported on the PR, not assumed here.

## 10. Gaps summary

| # | Gap | Impact on multi-statement DDL/DML |
| --- | --- | --- |
| G1 | `_ALLOWED_ROOTS` is SELECT-only | Every DDL/DML statement is rejected before execution. |
| G2 | Exactly one statement allowed | Scripts cannot be expressed. |
| G3 | `learner_ro` has no write privileges and is read-only by default | DDL/DML would fail with `42501` / `25006`. |
| G4 | Runner uses `DESCRIBE` + bounded subquery | Cannot execute DDL/DML; would double-execute DML. |
| G5 | Always `ROLLBACK` and no verifier hook | Cannot grade the state left by DML/DDL. |
| G6 | `public` is in the allowed schema set | A writable role could create objects in `public` if not changed. |
| G7 | `cleanup_datasets` is not wired to startup | Crashed shared-mode processes can leave `ds_*` schemas behind. |
| G8 | No startup requirement for `ephemeral` outside development | Writable SQL could run in the weaker shared mode in production. |
| G9 | Release Compose has no Docker socket | Ephemeral mode is not deployable there as written. |
| G10 | No DML/DDL feature keys in `sql_features.py` | Required-concept checks cannot express `insert`/`update`/`delete`/`create table`. |
