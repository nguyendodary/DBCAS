# 04 — Target Design: Safe Multi-Statement DDL/DML

This is a design, not an implementation. No code or migration is included in
this branch.

## 1. Principles

1. **Default deny.** A statement kind, schema, function, or clause is rejected
   unless the policy explicitly allows it.
2. **Two independent gates.** The AST policy rejects dangerous SQL before a
   connection is opened; PostgreSQL privileges reject anything the policy
   misses. Neither gate is trusted alone.
3. **One execution, one schema, one transaction.** A script runs in a private
   schema inside a disposable container, in a single transaction, and is
   always rolled back.
4. **No persistence.** The learner cannot leave a table, role, grant, or
   setting behind. The schema/container is destroyed even on error.
5. **Fail closed.** A parse error, unknown statement kind, ambiguous schema
   qualifier, or unsupported function aborts the whole script before execution.
6. **The server is authoritative.** The browser may display hints, but it
   never decides what is allowed.

## 2. Modes and gates

| Mode | Question setting | Sandbox requirement | Default |
| --- | --- | --- | --- |
| `read_only` | `question.sql_execution_mode = 'read_only'` | `shared` or `ephemeral` | **yes** |
| `read_write` | `question.sql_execution_mode = 'read_write'` | `ephemeral` outside development | no |
| `read_write` (dev only) | same | `shared` allowed only with `SQL_WRITABLE_SHARED_DEV=true` | no |

Startup rules (`Settings._deployment_safety` extension):

- If `deployment_mode != "development"` and any writable question can be
  served, require `sandbox_mode == "ephemeral"`. The simplest safe rule is:
  **if `SQL_WRITABLE_ENABLED=true` and `deployment_mode != "development"`,
  require `sandbox_mode == "ephemeral"`**, regardless of whether a writable
  question currently exists.
- If `sandbox_mode == "ephemeral"` and the Docker socket/image is unavailable,
  readiness fails; the API does not silently fall back to shared.
- `SQL_WRITABLE_ENABLED=false` (default) makes `read_write` questions return
  `422 sql_mode_disabled` rather than executing.

## 3. Role and privilege model

### 3.1 New role

Add a second login role, `learner_rw`, in `sandbox/init/00-learner-role.sh`
(and in the ephemeral container's init, which uses the same script):

```sql
CREATE ROLE learner_rw LOGIN PASSWORD :'learner_rw_password'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
ALTER ROLE learner_rw SET statement_timeout = :'statement_timeout';
ALTER ROLE learner_rw SET lock_timeout = '1s';
ALTER ROLE learner_rw SET idle_in_transaction_session_timeout = '15s';
ALTER ROLE learner_rw SET default_transaction_read_only = off;
ALTER ROLE learner_rw SET search_path = pg_catalog;
ALTER ROLE learner_rw SET temp_file_limit = '64MB';
ALTER ROLE learner_rw SET work_mem = '4MB';
ALTER ROLE learner_rw SET maintenance_work_mem = '16MB';
ALTER ROLE learner_rw SET max_parallel_workers_per_gather = 0;
REVOKE CREATE, USAGE ON SCHEMA public FROM PUBLIC;
REVOKE TEMPORARY ON DATABASE :"database_name" FROM PUBLIC;
REVOKE CREATE ON DATABASE :"database_name" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"database_name" TO learner_rw;
```

`learner_rw` deliberately has **no** `USAGE` on `public`, no `CREATE` on the
database, and no membership in `dbcas_dataset_setup` or any other role.

### 3.2 Per-execution schema

The admin connection creates the schema and hands ownership to `learner_rw`:

```sql
CREATE SCHEMA ds_<12 hex> AUTHORIZATION learner_rw;
```

The runner then sets, inside the transaction:

```sql
SET LOCAL search_path = ds_<12 hex>, pg_catalog;
```

Because the schema is owned by `learner_rw`, the learner can create/alter/drop
objects **inside it** without any cluster-wide `CREATE` privilege. The schema
is dropped by the admin after rollback, or dies with the container.

For the writable path, dataset setup runs as `learner_rw` (via `SET LOCAL ROLE`)
rather than `dbcas_dataset_setup`. This makes fixture tables owned by the same
role that the learner uses, so `ALTER TABLE` works. Setup SQL is still
admin-authored and validated by `dataset_setup.py`; it cannot escalate because
`learner_rw` is unprivileged.

### 3.3 Why not grant `CREATE` on `public`?

`public` is shared by every schema in the database. A writable learner with
`CREATE` on `public` could create objects that another session resolves through
`search_path`, or leave objects behind after a crash. The design removes
`public` from the allowed schema set for writable mode and revokes `CREATE`
from `PUBLIC`.

### 3.4 Defense in depth

Even if the AST policy misses a statement:

- the role cannot create schemas, roles, databases, extensions, foreign
  servers, or publications;
- the role cannot write outside its schema (no grants);
- the role cannot read `pg_catalog` through the policy, and has no special
  catalog privileges;
- the container has no network, no host mounts, a read-only rootfs, and a
  non-root UID;
- the transaction is rolled back and the container is destroyed.

## 4. Statement policy matrix

The parser uses `sqlglot.parse(sql_text, read="postgres")`. All statements are
parsed and checked **before** execution; if any statement fails, the whole
script is rejected.

### 4.1 Allowed roots

| Root | Allowed in `read_only` | Allowed in `read_write` | Notes |
| --- | --- | --- | --- |
| `Select` | yes | yes | Includes `VALUES`, `TABLE`, set operations, CTEs. |
| `Union` / `Intersect` / `Except` | yes | yes | Existing behavior. |
| `Subquery` | yes | yes | Existing behavior. |
| `Values` | yes | yes | Existing behavior. |
| `Insert` | no | yes | Own tables only; `RETURNING` allowed; `ON CONFLICT` allowed. |
| `Update` | no | yes | Own tables only; `FROM`/`RETURNING` allowed. |
| `Delete` | no | yes | Own tables only; `USING`/`RETURNING` allowed. |
| `Create` (TABLE/VIEW/INDEX) | no | yes | Explicit columns; no storage properties; no `AS SELECT` from outside own schema. |
| `Alter` (TABLE) | no | yes | Only the subcommands in §4.4. |
| `Drop` (TABLE/VIEW/INDEX) | no | yes | Own objects only; `IF EXISTS` allowed. |
| `TruncateTable` | no | yes | Own tables only; no `RESTART IDENTITY`; `CASCADE` allowed only within own schema. |

Everything else is rejected, including `Merge`, `Command`, `Transaction`,
`Set`, `Copy`, `Grant`, `Revoke`, `Analyze`, `Describe`, `Pragma`, `Lock`,
`Into`, `UserDefinedFunction`, and all `Create` kinds not listed above.

### 4.2 Always forbidden

- `BEGIN`, `COMMIT`, `ROLLBACK`, `SAVEPOINT`, `RELEASE`, `START TRANSACTION`,
  `PREPARE TRANSACTION`, `COMMIT PREPARED`, `ROLLBACK PREPARED`.
- `SET`, `RESET`, `DISCARD`, `LOAD`, `SET ROLE`, `SET SESSION AUTHORIZATION`.
- `COPY`, `\copy` (never reaches the server), `DO`, `CALL`, `EXECUTE`,
  `PREPARE`, `DECLARE`, `FETCH`, `MOVE`, `CLOSE`.
- `GRANT`, `REVOKE`, `ALTER DEFAULT PRIVILEGES`, `REASSIGN OWNED`,
  `DROP OWNED`.
- `CREATE ROLE/USER/GROUP`, `ALTER ROLE`, `DROP ROLE`, `CREATE DATABASE`,
  `DROP DATABASE`, `CREATE TABLESPACE`, `DROP TABLESPACE`, `ALTER SYSTEM`.
- `CREATE EXTENSION`, `CREATE LANGUAGE`, `CREATE FOREIGN TABLE`,
  `CREATE SERVER`, `CREATE USER MAPPING`, `IMPORT FOREIGN SCHEMA`,
  `CREATE PUBLICATION`, `CREATE SUBSCRIPTION`, `CREATE EVENT TRIGGER`.
- `CREATE FUNCTION`, `CREATE PROCEDURE`, `CREATE AGGREGATE`, `CREATE OPERATOR`,
  `CREATE CAST`, `CREATE TYPE`, `CREATE DOMAIN`, `CREATE COLLATION`,
  `CREATE TEXT SEARCH ...`, `CREATE STATISTICS`, `CREATE TRANSFORM`,
  `CREATE ACCESS METHOD`.
- `CREATE TRIGGER`, `CREATE RULE`, `CREATE POLICY`, `SECURITY LABEL`,
  `COMMENT ON`.
- `VACUUM`, `ANALYZE`, `CLUSTER`, `REINDEX`, `CHECKPOINT`,
  `REFRESH MATERIALIZED VIEW`, `EXPLAIN`, `SHOW`.
- `LISTEN`, `NOTIFY`, `UNLISTEN`, `LOCK TABLE`.
- `CREATE TEMP/TEMPORARY TABLE`, `UNLOGGED`, `CREATE SEQUENCE`,
  `ALTER SEQUENCE`, `DROP SEQUENCE`, `nextval`, `setval`.
- `SELECT ... INTO`, `SELECT ... FOR UPDATE/SHARE`, `TABLE ...` if it resolves
  to a forbidden object.
- Any reference to `pg_catalog`, `pg_toast`, `information_schema`, `pg_temp`,
  another `ds_*` schema, or `public` (in writable mode).
- Any `pg_*` or `sql_*` unqualified object/function name.

### 4.3 Schema and name rules

- Writable mode allowed schema set: `{session_schema}` only. Unqualified names
  resolve through `search_path` = session schema, `pg_catalog`.
- Reject a table/column qualifier that is `public`, `pg_catalog`,
  `information_schema`, `pg_temp*`, any `ds_*` other than the session schema,
  or any other schema.
- Reject `catalog` (cross-database) qualifiers.
- Reject `CREATE TABLE public.x`, `ALTER TABLE public.x`, `DROP TABLE public.x`
  even if the role would deny it; fail early with a policy error.
- Reject `REFERENCES`/`FROM`/`USING`/subqueries that resolve outside the
  session schema.

### 4.4 `ALTER TABLE` subcommands

Allow:

- `ADD [COLUMN] ...` with a type, nullability, and a constant `DEFAULT`;
- `DROP [COLUMN] ...`;
- `RENAME [COLUMN] ... TO ...`;
- `ALTER [COLUMN] ... TYPE ... [USING <simple expression>]`;
- `ALTER [COLUMN] ... SET/DROP DEFAULT`;
- `ALTER [COLUMN] ... SET/DROP NOT NULL`;
- `ADD CONSTRAINT` for `CHECK`, `UNIQUE`, `PRIMARY KEY`, `FOREIGN KEY`
  referencing own tables only;
- `DROP CONSTRAINT ...`;
- `RENAME TO ...`.

Reject:

- `SET SCHEMA`, `OWNER TO`, `SET TABLESPACE`, `SET LOGGED/UNLOGGED`;
- `ENABLE/DISABLE TRIGGER`, `ENABLE/DISABLE RULE`;
- `INHERIT`, `NO INHERIT`, `OF`, `NOT OF`;
- `ATTACH/DETACH PARTITION`, `PARTITION BY`;
- `ADD COLUMN ... GENERATED ...` (generated columns) in v1;
- any `USING` expression containing a subquery, function, or column from
  another table.

### 4.5 `CREATE TABLE` restrictions

Allow:

- explicit column list with built-in types;
- `PRIMARY KEY`, `UNIQUE`, `CHECK` (simple expressions), `FOREIGN KEY`
  referencing own tables, `NOT NULL`, constant `DEFAULT`;
- `CREATE TABLE ... AS SELECT ...` only when every source is in the session
  schema (or a `VALUES` list);
- `CREATE VIEW ... AS SELECT ...` with the same source restriction;
- `CREATE [UNIQUE] INDEX ... ON <own table> (...)` without `CONCURRENTLY`,
  `TABLESPACE`, or `INCLUDE` outside own columns.

Reject:

- `LIKE` from outside the session schema;
- `INHERITS`, `PARTITION BY`, `OF`, `ON COMMIT`, `TABLESPACE`,
  `USING <access method>`, `WITH (...)` storage parameters;
- `UNLOGGED`, `TEMPORARY`;
- `GENERATED ... AS IDENTITY` and `SERIAL` in v1 (sequences are blocked);
- `DEFAULT` containing a function call (constants and
  `CURRENT_DATE/TIME/TIMESTAMP` only);
- `CHECK` containing a subquery or function call;
- `REFERENCES` to a table outside the session schema;
- `CREATE INDEX CONCURRENTLY`;
- `CREATE MATERIALIZED VIEW` (not in v1);
- `CREATE TABLE ... AS EXECUTE`.

### 4.6 Function policy

Reuse the existing deny-list (`sql_validator.py:70-109`) and keep the
`pg_*`/`sql_*` prefix ban. For writable mode, additionally:

- allow only built-in, side-effect-free functions in `SELECT`, `WHERE`,
  `DEFAULT` (constants only), and `CHECK` expressions;
- reject all `Anonymous` functions not on an explicit allow-list in `CHECK`,
  `DEFAULT`, and `USING` expressions;
- reject `nextval`, `setval`, `currval`, `lastval`, `set_config`,
  `current_setting`, `pg_sleep`, `pg_notify`, `dblink*`, `lo_*`, `xml_*`,
  `pg_read_*`, `pg_write_*`, `pg_ls_*`, `pg_stat_*`, `pg_terminate_*`,
  `inet_*`, `txid_*`;
- document that `pg_typeof`, `pg_size_pretty`, and similar `pg_*` helpers are
  unavailable; this is a deliberate compatibility trade-off.

## 5. Execution protocol

New method: `execute_script(sql_text, *, schema, policy) -> ScriptResult`.

1. **Validate** the whole script (parse + policy). Return a structured
   `validation_error` with `statement_index`, `line`, `column`, and a stable
   `error_type`. No connection is opened.
2. **Connect** as `learner_rw`:
   - ephemeral: through `app.sandbox_job` inside the container;
   - shared (dev only): direct psycopg connection.
3. **Configure** the session:
   ```sql
   SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;
   SET statement_timeout = <per_statement_ms>;
   SET lock_timeout = 1000;
   SET idle_in_transaction_session_timeout = 15000;
   SET search_path = <schema>, pg_catalog;
   SET max_parallel_workers_per_gather = 0;
   ```
4. **Begin** one transaction.
5. **Execute statements sequentially**:
   - for each statement, set
     `SET LOCAL statement_timeout = min(per_statement_ms, remaining_script_ms)`;
   - execute once, never through a `DESCRIBE` wrapper;
   - if `cursor.description` is present, stream rows with a server-side cursor
     and enforce row/byte/cell limits;
   - if not, capture `cursor.statusmessage` and `cursor.rowcount`;
   - enforce `max_dml_rows` per statement and per script;
   - enforce the script wall-clock budget between statements;
   - on any error, stop immediately.
6. **Verify** (grading only): run the trusted `verifier_sql` in the same
   transaction, as a separate read-only cursor, with the same `search_path`.
7. **Rollback** always. Never commit learner changes.
8. **Drop** the schema (shared) or destroy the container (ephemeral).

### 5.1 Result shape

```json
{
  "success": true,
  "mode": "read_write",
  "rolled_back": true,
  "execution_time_ms": 42,
  "statements": [
    {"index": 1, "kind": "create_table", "command": "CREATE TABLE", "row_count": 0},
    {"index": 2, "kind": "insert", "command": "INSERT 0 3", "row_count": 3},
    {"index": 3, "kind": "select", "command": "SELECT 3", "row_count": 3,
     "columns": ["id"], "column_types": ["number"], "rows": [[1], [2], [3]]}
  ],
  "columns": ["id"], "column_types": ["number"], "rows": [[1], [2], [3]],
  "row_count": 3
}
```

The top-level `columns`/`rows`/`row_count` mirror the **last row-returning
statement**, so the existing frontend keeps working. `statements` is additive.

### 5.2 Statement budget

- `max_statements`: 32 (read/write), 32 (read-only scripts).
- `max_sql_bytes`: 16,000 (existing `SQL_ANSWER_MAX_LEN`).
- `max_script_ms`: 5,000 wall clock.
- `per_statement_ms`: 3,000 (existing cap).
- `max_rows`: 1,000 per result set; 2,000 across the script.
- `max_result_bytes`: 256 KiB per result set; 512 KiB across the script.
- `max_cell_bytes`: 16 KiB.
- `max_dml_rows`: 10,000 per statement; 50,000 per script.
- `max_objects`: 64 objects in the session schema.
- `max_connections`: 2 per ephemeral container; 4 concurrent scripts per API
  process in shared dev mode.

### 5.3 Timeout and cancellation

- `statement_timeout` cancels a single runaway statement.
- The script budget is enforced before each statement; because each statement
  is capped at 3 s, the worst case is bounded.
- `lock_timeout` prevents a DDL lock wait from consuming the budget.
- `idle_in_transaction_session_timeout` closes abandoned transactions.
- On timeout, the runner cancels the statement, rolls back, and returns
  `error_type="timeout"` with the failing statement index.
- The ephemeral watchdog kills the container at the lifetime limit even if the
  Python process is stuck (`ephemeral_sandbox.py:83-114`).

## 6. Error model

Map SQLSTATE to stable, sanitized errors:

| SQLSTATE | `error_type` | Message |
| --- | --- | --- |
| `25006` | `prohibited_statement` | "This statement is not allowed in the sandbox" |
| `42501` | `forbidden_object` | "You do not have permission to access that object" |
| `42P01` | `undefined_table` | `relation "<name>" does not exist` |
| `42703` | `undefined_column` | `column "<name>" does not exist` |
| `23505` | `unique_violation` | `duplicate key value violates unique constraint "<name>"` |
| `23503` | `foreign_key_violation` | `insert or update violates foreign key constraint "<name>"` |
| `23514` | `check_violation` | `new row violates check constraint "<name>"` |
| `22P02` | `invalid_input` | `invalid input syntax for type <type>` |
| `22001` | `value_too_long` | `value too long for type <type>` |
| `57014` | `timeout` | "The statement exceeded the execution time limit" |
| `55P03` | `lock_timeout` | "The statement could not acquire a lock in time" |
| `53200` | `out_of_memory` | "The statement exceeded the sandbox memory limit" |
| `53100` | `disk_full` | "The sandbox ran out of temporary storage" |
| `54000` | `program_limit` | "The statement exceeded a PostgreSQL limit" |
| other | `execution_error` | "The statement could not be executed" |

Sanitization rules:

- strip the internal `ds_*` schema name and replace it with `your_schema`;
- never include the container id, host, port, role name, file path, or
  connection string;
- include `statement_index`, `line`, and `column` when available;
- log the full SQLSTATE and a hash of the SQL server-side, not in the API
  response.

## 7. Grading model

Add a per-dataset `grading_mode`:

| Mode | How it works | Use for |
| --- | --- | --- |
| `result` (default) | Compare the last row-returning statement to `expected_result`. | `SELECT`, `INSERT/UPDATE/DELETE ... RETURNING`. |
| `state` | Run a trusted `verifier_sql` after the script, in the same transaction; compare its result to `expected_result`. | `INSERT/UPDATE/DELETE` without `RETURNING`, `ALTER`, `CREATE`. |
| `script` | Compare per-statement command tags/row counts to an expected list. | "Create a table and insert exactly 3 rows" process checks. |

`verifier_sql` is admin-authored, stored in `sql_test_dataset.verifier_sql`,
and validated as a read-only `SELECT` with the same schema restrictions. It
runs **after** the learner script, **before** rollback, so it sees the
uncommitted state.

### 7.1 Grading integrity caveat

A learner can create a view/table with the same name as a fixture object, or
insert rows that happen to match the expected output. `state` mode should:

- check that each verifier source is an ordinary table (`relkind='r'`) or a
  view created by the fixture, not a learner replacement;
- compare column names/types before comparing rows;
- for DDL exercises, verify catalog facts (table exists, column type,
  constraint exists) rather than only data;
- flag `state`/`script` modes as **review-recommended** for high-stakes
  assessments.

This limitation is inherent to automated writable-SQL grading and must be a
product decision (`07-unknowns.md`).

### 7.2 Required concepts

Extend `sql_features.py` with feature keys:

- `insert`, `update`, `delete`, `create_table`, `alter_table`, `drop`,
  `constraint`, `index`, `transaction` (the last only if transaction control
  is ever allowed; it is not in v1).

Map concept-name fragments (`"insert"`, `"update"`, `"delete"`, `"create
table"`, `"alter table"`, `"primary key"`, `"foreign key"`, `"index"`) to
those keys. Keep the existing "unverified concept does not change the score"
behavior.

## 8. Resource limits and DoS controls

| Resource | Control |
| --- | --- |
| CPU | `--cpus 1`; `max_parallel_workers_per_gather=0`; 3 s statement timeout. |
| Memory | 256 MB container (SELECT) / **512 MB recommended for writable**; `work_mem=4MB`; `maintenance_work_mem=16MB`; `shared_buffers=16MB`. |
| Disk | 192 MB tmpfs data + 8 MB tmp; `temp_file_limit=64MB`; `max_dml_rows`; 64-object cap. |
| Connections | 2 per ephemeral container; 4 concurrent scripts per API process in shared dev mode; `sandbox_busy` 503 when full. |
| Locks | `lock_timeout=1s`; single transaction; no `LOCK TABLE`. |
| Runaway queries | `statement_timeout=3s`; 5 s script budget; watchdog. |
| Repeated abuse | Per-account rate limit (reuse the `practice_preview_rate_limit_*` pattern); `sql_run_rate_limit_attempts=30/60s` suggested. |
| Stale state | Always rollback; drop schema; ephemeral `--rm`; startup `cleanup_datasets()`; periodic sweep. |

Writable mode raises the memory recommendation because DDL/DML can materialize
more than a single `SELECT`. The exact 256 vs 512 MB choice must be validated
with the test matrix in `06-delivery-plan.md`.

## 9. API and UI changes

### API

- Keep `POST /sessions/{session_id}/sql-run`.
- Derive `mode` from the question, never from the request body.
- Add to `SqlRunResult`:
  - `mode: "read_only" | "read_write"`;
  - `rolled_back: bool`;
  - `statements: list[StatementResult]`;
  - `error_statement_index: int | None`;
  - `error_line: int | None`, `error_column: int | None`.
- Defaults keep old clients compatible.
- Add `422 sql_mode_disabled` when writable mode is off; `503 sandbox_busy`
  when the executor is at capacity.

### UI

- Editor toolbar: `Run` (selection or whole script) and a read-only/writable
  badge.
- Results panel: a grid for the last row-returning statement, plus a
  "Messages" tab showing `CREATE TABLE`, `INSERT 0 3`, etc.
- Writable mode shows a persistent notice: "Changes are rolled back after the
  run. Nothing is saved."
- Errors highlight the failing line/statement.
- The editor must not claim DDL/DML works when the question is `read_only`;
  show a hint instead.

## 10. Data model changes (design only)

Migration `029_sql_writable_grading.sql` (additive):

```sql
ALTER TABLE question
  ADD COLUMN sql_execution_mode VARCHAR(16) NOT NULL DEFAULT 'read_only'
  CHECK (sql_execution_mode IN ('read_only', 'read_write'));

ALTER TABLE sql_test_dataset
  ADD COLUMN grading_mode VARCHAR(16) NOT NULL DEFAULT 'result'
  CHECK (grading_mode IN ('result', 'state', 'script'));

ALTER TABLE sql_test_dataset
  ADD COLUMN verifier_sql TEXT;
```

No existing column changes; old rows keep `read_only` / `result`. A separate
migration is preferred over editing `db/schema.sql` alone so existing
databases upgrade deterministically.

Optional audit table (only if policy requires it):

```sql
CREATE TABLE sql_execution_event (
  event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id INT NOT NULL REFERENCES account(account_id),
  session_id INT,
  question_id INT,
  mode VARCHAR(16) NOT NULL,
  statement_count SMALLINT NOT NULL,
  duration_ms INT NOT NULL,
  outcome VARCHAR(32) NOT NULL,
  error_type VARCHAR(64),
  sql_hash CHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Store a SHA-256 of the SQL, not the SQL text, unless the privacy owner
approves text retention.

## 11. Observability

Metrics:

- `sql_run_total{mode,outcome}`;
- `sql_run_duration_seconds{mode}` (histogram);
- `sql_run_statements{mode}` (histogram);
- `sql_validation_reject_total{reason}`;
- `sql_policy_violation_total{rule}`;
- `sql_sandbox_busy_total`;
- `sql_sandbox_startup_seconds`;
- `sql_sandbox_oom_total`.

Logs (structured, no SQL text):

- `request_id`, `account_id_hash`, `session_id`, `question_id`, `mode`,
  `statement_count`, `duration_ms`, `outcome`, `error_type`, `sql_hash`;
- `WARN` for policy violations and privilege errors;
- `ERROR` for sandbox unavailable, OOM, watchdog kill, cleanup failure.

Alerts:

- sandbox unavailable rate > 1% over 5 min;
- p95 run duration > 5 s;
- any `sandbox_cleanup_failed`;
- container OOM/exit rate > 0.1%;
- validation-reject spike (possible attack or broken question).

## 12. Compatibility and migration

- Existing questions: `read_only`; behavior unchanged.
- Existing datasets: `grading_mode='result'`; `verifier_sql=NULL`.
- Existing `learner_ro` role and grants: unchanged.
- New `learner_rw` role: created by the init script; for existing shared
  sandbox volumes, a one-time `ALTER/CREATE ROLE` migration is needed (the
  init script only runs on a fresh volume). The application can also ensure
  the role idempotently at startup, as `provision_dataset` already does for
  `dbcas_dataset_setup` (`sandbox_runner.py:299-303`).
- Existing shared volumes have `public` grants that must be tightened before
  writable mode is enabled; the startup check should verify
  `has_schema_privilege('learner_rw','public','CREATE') = false`.
- Rollback: set `SQL_WRITABLE_ENABLED=false`; the new columns are additive and
  can stay. No data migration is required.

## 13. What must not change

- The app DB and sandbox DB must remain on distinct servers
  (`config.py:220-221`).
- `learner_ro` remains SELECT-only and `default_transaction_read_only=on`.
- The SELECT-only path keeps its current limits and rollback behavior.
- `docs/qa/**` is out of scope.
- No learner SQL is ever sent to the app DB connection.
