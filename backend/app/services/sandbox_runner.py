"""Sandbox Runner — executes untrusted learner SQL in the isolated Docker
PostgreSQL sandbox (UC13, FR-09, QA02, QA03, NFR-02, TC02).

The runner talks to the dedicated ``sandbox`` compose service — never to the
system database. Learner statements run as the read-only ``learner_ro`` role
inside an explicit ``READ ONLY`` transaction that is always rolled back, so no
state leaks between attempts (RSK-01). Test datasets are provisioned into a
dedicated per-execution schema by a separate admin connection; the learner
role only holds SELECT on those tables, and the schema is dropped right after
evaluation.

Nothing in this module leaks container or connection details: callers receive
a sanitized :class:`SandboxResult` whose errors are classified into stable
``error_type`` codes with learner-safe messages only.
"""

import logging
import json
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import psycopg
import sqlglot
from psycopg import sql as pgsql

from ..config import Settings
from .sql_validator import validate_learner_sql
from .sql_classifier import classify_script, validate_read_only_script, validate_writable_script
from .dataset_setup import validated_setup_statements

logger = logging.getLogger(__name__)

DATASET_SCHEMA_PREFIX = "ds_"


class SandboxError(Exception):
    """Infrastructure-level sandbox failure (provisioning, connectivity).

    Carries a stable machine code and a sanitized message — never SQLSTATE
    internals or connection strings.
    """

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class SandboxResult:
    """Structured, typed result of one learner statement execution."""

    success: bool
    columns: list[str] = field(default_factory=list)
    column_types: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: int = 0
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    # Additive fields for multi-statement runs; defaults keep legacy callers.
    mode: str = "read_only"
    statements: list[dict] = field(default_factory=list)
    error_statement_index: Optional[int] = None
    error_line: Optional[int] = None
    error_column: Optional[int] = None
    rolled_back: bool = True
    table_states: list[dict] = field(default_factory=list)


def _jsonable(value: Any) -> Any:
    """Convert a psycopg row value into a JSON-serializable one."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).hex()
    # Decimal, date/time, uuid, … — str() is stable and readable.
    return str(value)


def _classify_error(exc: psycopg.Error, timeout_ms: int) -> tuple[str, str]:
    """Map a database error to (error_type, learner-safe message)."""
    sqlstate = getattr(exc, "sqlstate", None) or ""
    primary = getattr(exc.diag, "message_primary", None) or str(exc)

    if sqlstate == "57014":  # query_canceled — statement_timeout is the source
        return "timeout", f"Query exceeded the {timeout_ms / 1000:g}-second statement timeout"
    if sqlstate == "55P03":  # lock_not_available
        return "lock_timeout", "The statement could not acquire a lock in time"
    if sqlstate == "53200":  # out_of_memory
        return "out_of_memory", "The statement exceeded the sandbox memory limit"
    if sqlstate == "53100":  # disk_full
        return "disk_full", "The sandbox ran out of temporary storage"
    if sqlstate == "54000":  # program_limit_exceeded
        return "program_limit", "The statement exceeded a PostgreSQL limit"
    if sqlstate == "25006":  # read_only_sql_transaction
        return "prohibited_statement", "Only read-only SELECT queries are allowed"
    if sqlstate in {"42601", "42602", "42622"}:
        return "syntax_error", primary
    if sqlstate == "42501":
        return "permission_denied", primary

    if sqlstate.startswith("42"):  # undefined table/column/function etc.
        return "schema_error", primary
    if sqlstate.startswith("23"):  # integrity violations (defensive: writes are blocked)
        return "execution_error", primary
    if sqlstate.startswith(("08", "53")):  # connection / insufficient resources
        return "sandbox_unavailable", "The SQL sandbox is unavailable"
    return "execution_error", primary


class SandboxRunner:
    """Runs learner SQL against the isolated sandbox container.

    Two connections are used:

    * ``sandbox_url`` — the unprivileged ``learner_ro`` role that executes
      untrusted statements inside a rolled-back READ ONLY transaction.
    * ``sandbox_admin_url`` — the privileged role used only to create,
      populate and drop per-execution dataset schemas. It never executes
      learner SQL.
    """

    def __init__(self, settings: Settings):
        self._learner_url = settings.sandbox_url
        self._writable_url = settings.sandbox_writable_url
        self._admin_url = settings.sandbox_admin_url
        self._learner_role = settings.sandbox_learner_role
        self._writable = settings.sandbox_writable
        self._timeout_ms = settings.sandbox_statement_timeout_ms
        self._max_rows = settings.sandbox_max_rows
        self._max_sql_bytes = settings.sandbox_max_sql_bytes
        self._max_result_bytes = settings.sandbox_max_result_bytes
        self._max_cell_bytes = settings.sandbox_max_cell_bytes
        self._max_setup_bytes = settings.sandbox_max_setup_bytes
        self._connect_timeout = settings.sandbox_connect_timeout_seconds
        # Multi-statement script budgets (used only behind the opt-in flag).
        self._multi_enabled = settings.sandbox_multi_statement
        self._max_statements = settings.sandbox_max_statements
        self._max_script_ms = settings.sandbox_max_script_ms
        self._max_rows_script = settings.sandbox_max_rows_per_script
        self._max_bytes_script = settings.sandbox_max_result_bytes_per_script

    def _connect(self, url, **options):
        """One transient reconnect before any SQL, within the same budget.

        libpq needs at least two seconds per connection attempt. Small budgets
        keep their single attempt; authentication and query errors never retry.
        """
        budget = self._connect_timeout
        first = budget // 2 if budget >= 4 else budget
        began = time.monotonic()
        try:
            return psycopg.connect(url, connect_timeout=first, **options)
        except psycopg.OperationalError as exc:
            transient = (
                isinstance(exc, psycopg.errors.ConnectionTimeout)
                or (exc.sqlstate or "").startswith("08")
                or exc.sqlstate == "57P03"
                or any(message in str(exc).lower() for message in (
                    "server closed the connection unexpectedly",
                    "connection reset by peer",
                ))
            )
            if not transient:
                raise
            remaining = int(budget - (time.monotonic() - began))
            if budget < 4 or remaining < 2:
                raise
            return psycopg.connect(url, connect_timeout=remaining, **options)

    def is_ready(self) -> bool:
        """Probe only the configured learner connection, without dataset writes."""
        try:
            with self._connect(self._learner_url) as conn:
                conn.execute("BEGIN READ ONLY")
                ready = conn.execute("SELECT 1").fetchone() == (1,)
                conn.rollback()
                return ready
        except psycopg.Error:
            return False

    # ---------- learner execution ----------

    def execute(self, sql_text: str, *, schema: Optional[str] = None) -> SandboxResult:
        """Execute one learner statement inside a READ ONLY transaction.

        The transaction is always rolled back. ``schema`` optionally scopes
        the search_path to a provisioned dataset schema.
        """
        sql_text = (sql_text or "").strip()
        if not sql_text:
            return SandboxResult(
                success=False, error_type="empty_query", error_message="Query is empty"
            )
        if len(sql_text.encode("utf-8")) > self._max_sql_bytes:
            return SandboxResult(
                success=False,
                error_type="query_too_large",
                error_message=f"Query exceeds the {self._max_sql_bytes}-byte limit",
            )
        issue = validate_learner_sql(
            sql_text, allowed_schemas=frozenset({schema}) if schema else frozenset()
        )
        if issue:
            error_type, message = issue
            return SandboxResult(
                success=False, error_type=error_type, error_message=message
            )

        try:
            conn = self._connect(
                self._learner_url,
                autocommit=True,
            )
        except (psycopg.OperationalError, OSError) as exc:
            logger.warning("sandbox connect failed: %s", type(exc).__name__)
            return SandboxResult(
                success=False,
                error_type="sandbox_unavailable",
                error_message="The SQL sandbox is unavailable",
            )

        started: Optional[float] = None
        try:
            conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
            conn.execute(f"SET statement_timeout = {self._timeout_ms}")
            conn.execute(
                f"SET idle_in_transaction_session_timeout = {self._timeout_ms * 4}"
            )
            if schema:
                conn.execute(
                    pgsql.SQL("SET search_path TO {}").format(
                        pgsql.Identifier(schema)
                    )
                )
            conn.execute("BEGIN")
            started = time.perf_counter()
            # DECLARE/DESCRIBE obtains shape without transferring query rows.
            canonical = sqlglot.parse_one(sql_text, read="postgres").sql(dialect="postgres")
            with conn.cursor(name="shape_" + uuid.uuid4().hex[:12]) as shape:
                shape.execute(canonical)
                descriptions = list(shape.description or [])
            columns = [d.name for d in descriptions]
            if len(columns) > 128:
                return SandboxResult(False, error_type="result_too_large", error_message="Result exceeds the 128-column limit")
            column_types = ["number" if d.type_code in {20,21,23,700,701,1700} else "boolean" if d.type_code == 16 else "text" for d in descriptions]
            names = [f"c{i}" for i in range(len(columns))]
            size_terms = [f"COALESCE(octet_length(_r.{n}::text),0)" for n in names]
            size = " + ".join(size_terms) or "0"
            overflow = " OR ".join(f"{t} > {self._max_cell_bytes}" for t in size_terms) or "false"
            overflow = f"({overflow}) OR ({size}) > {self._max_result_bytes}"
            projection = ", ".join(f"CASE WHEN {overflow} THEN NULL ELSE _r.{n} END" for n in names)
            output = f"{projection}, " if projection else ""
            alias = f"_r({','.join(names)})" if names else "_r"
            bounded = f"SELECT {output}({overflow}) AS _oversized FROM ({canonical}) AS {alias} LIMIT {self._max_rows + 1}"
            rows = []
            used_bytes = len(json.dumps(columns).encode())
            with conn.cursor(name="bounded_" + uuid.uuid4().hex[:12]) as cur:
                cur.execute(bounded)
                while (row := cur.fetchone()) is not None:
                    if time.perf_counter() - started > self._timeout_ms / 1000:
                        return SandboxResult(False, error_type="timeout", error_message="Query exceeded the execution time limit")
                    if row[-1]:
                        return SandboxResult(False, error_type="result_too_large", error_message="Result exceeds the cell or serialized-byte limit")
                    values = [_jsonable(v) for v in row[:-1]]
                    used_bytes += len(json.dumps(values, ensure_ascii=False, default=str).encode()) + 1
                    if len(rows) >= self._max_rows or used_bytes > self._max_result_bytes:
                        return SandboxResult(False, error_type="result_too_large", error_message="Result exceeds the row or serialized-byte limit")
                    rows.append(values)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            conn.execute("ROLLBACK")
            return SandboxResult(
                success=True,
                columns=columns,
                column_types=column_types,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=elapsed_ms,
            )
        except psycopg.Error as exc:
            elapsed_ms = (
                int((time.perf_counter() - started) * 1000) if started is not None else 0
            )
            error_type, message = _classify_error(exc, self._timeout_ms)
            return SandboxResult(
                success=False,
                execution_time_ms=elapsed_ms,
                error_type=error_type,
                error_message=message,
            )
        finally:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            conn.close()

    # ---------- multi-statement read-only scripts (opt-in) ----------

    def _read_bounded(self, conn, canonical: str, timeout_ms: int, started: float,
                      row_budget: int, byte_budget: int):
        """Stream one read-only statement through named cursors with caps.

        Returns ``(columns, column_types, rows, error_type, error_message)``.
        The SQL-level size guards keep a single oversized cell from ever being
        transferred to the API process.
        """
        with conn.cursor(name="shape_" + uuid.uuid4().hex[:12]) as shape:
            shape.execute(canonical)
            descriptions = list(shape.description or [])
        columns = [d.name for d in descriptions]
        if len(columns) > 128:
            return [], [], [], "result_too_large", "Result exceeds the 128-column limit"
        column_types = [
            "number" if d.type_code in {20, 21, 23, 700, 701, 1700}
            else "boolean" if d.type_code == 16 else "text"
            for d in descriptions
        ]
        names = [f"c{i}" for i in range(len(columns))]
        size_terms = [f"COALESCE(octet_length(_r.{n}::text),0)" for n in names]
        size = " + ".join(size_terms) or "0"
        overflow = " OR ".join(f"{t} > {self._max_cell_bytes}" for t in size_terms) or "false"
        overflow = f"({overflow}) OR ({size}) > {min(self._max_result_bytes, byte_budget)}"
        projection = ", ".join(
            f"CASE WHEN {overflow} THEN NULL ELSE _r.{n} END" for n in names
        )
        output = f"{projection}, " if projection else ""
        alias = f"_r({','.join(names)})" if names else "_r"
        limit = min(self._max_rows, row_budget) + 1
        bounded = (
            f"SELECT {output}({overflow}) AS _oversized "
            f"FROM ({canonical}) AS {alias} LIMIT {limit}"
        )
        rows: list[list] = []
        used_bytes = len(json.dumps(columns).encode())
        with conn.cursor(name="bounded_" + uuid.uuid4().hex[:12]) as cur:
            cur.execute(bounded)
            while (row := cur.fetchone()) is not None:
                if time.perf_counter() - started > timeout_ms / 1000:
                    return columns, column_types, rows, "timeout", "Query exceeded the execution time limit"
                if row[-1]:
                    return (columns, column_types, rows, "result_too_large",
                            "Result exceeds the cell or serialized-byte limit")
                values = [_jsonable(v) for v in row[:-1]]
                used_bytes += len(json.dumps(values, ensure_ascii=False, default=str).encode()) + 1
                if len(rows) >= min(self._max_rows, row_budget) or used_bytes > byte_budget:
                    return (columns, column_types, rows, "result_too_large",
                            "Result exceeds the row or serialized-byte limit")
                rows.append(values)
        return columns, column_types, rows, None, None

    def execute_script(self, sql_text: str, *, schema: Optional[str] = None) -> SandboxResult:
        """Execute a validated multi-statement *read-only* script.

        One READ ONLY transaction, one statement at a time, always rolled back.
        Per-statement results and the failing statement index are reported; the
        top-level rows mirror the last row-returning statement so existing
        clients keep working. No new privileges or connections are introduced.
        """
        sql_text = (sql_text or "").strip()
        if not sql_text:
            return SandboxResult(success=False, error_type="empty_query", error_message="Query is empty")
        if len(sql_text.encode("utf-8")) > self._max_sql_bytes:
            return SandboxResult(
                success=False, error_type="query_too_large",
                error_message=f"Query exceeds the {self._max_sql_bytes}-byte limit",
            )
        issue = validate_read_only_script(
            sql_text,
            allowed_schemas=frozenset({schema}) if schema else frozenset(),
            max_statements=self._max_statements,
        )
        if issue:
            error_type, message, index = issue
            return SandboxResult(
                success=False, error_type=error_type, error_message=message,
                error_statement_index=index,
            )

        try:
            conn = self._connect(self._learner_url, autocommit=True)
        except (psycopg.OperationalError, OSError) as exc:
            logger.warning("sandbox connect failed: %s", type(exc).__name__)
            return SandboxResult(success=False, error_type="sandbox_unavailable",
                                 error_message="The SQL sandbox is unavailable")

        script_started = time.perf_counter()
        statements: list[dict] = []
        rows_used = 0
        bytes_used = 0
        try:
            conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
            conn.execute(f"SET statement_timeout = {self._timeout_ms}")
            conn.execute(f"SET idle_in_transaction_session_timeout = {self._timeout_ms * 4}")
            if schema:
                conn.execute(pgsql.SQL("SET search_path TO {}").format(pgsql.Identifier(schema)))
            conn.execute("BEGIN")

            classification = classify_script(sql_text, max_statements=self._max_statements)
            if not classification.ok:
                return SandboxResult(
                    success=False, error_type=classification.error_type,
                    error_message=classification.error_message,
                )

            for stmt in classification.statements:
                elapsed_ms = (time.perf_counter() - script_started) * 1000
                if elapsed_ms > self._max_script_ms:
                    return SandboxResult(
                        success=False, error_type="timeout",
                        error_message="Script exceeded the execution time limit",
                        statements=statements, error_statement_index=stmt.index,
                        execution_time_ms=int(elapsed_ms),
                    )
                remaining = max(1, int(self._max_script_ms - elapsed_ms))
                timeout_ms = min(self._timeout_ms, remaining)
                conn.execute(f"SET LOCAL statement_timeout = {timeout_ms}")
                stmt_started = time.perf_counter()
                canonical = stmt.sql.rstrip().rstrip(";")
                try:
                    columns, column_types, rows, err_type, err_msg = self._read_bounded(
                        conn, canonical, timeout_ms, script_started,
                        max(0, self._max_rows_script - rows_used),
                        max(0, self._max_bytes_script - bytes_used),
                    )
                except psycopg.Error as exc:
                    err_type, err_msg = _classify_error(exc, timeout_ms)
                    columns, column_types, rows = [], [], []
                stmt_ms = int((time.perf_counter() - stmt_started) * 1000)
                entry = {
                    "index": stmt.index,
                    "kind": stmt.kind,
                    "command": "SELECT" if columns else "",
                    "row_count": len(rows),
                    "columns": columns,
                    "column_types": column_types,
                    "rows": rows,
                    "execution_time_ms": stmt_ms,
                }
                if err_type:
                    entry.update(error_type=err_type, error_message=err_msg)
                    statements.append(entry)
                    return SandboxResult(
                        success=False, error_type=err_type, error_message=err_msg,
                        statements=statements, error_statement_index=stmt.index,
                        execution_time_ms=int((time.perf_counter() - script_started) * 1000),
                    )
                statements.append(entry)
                rows_used += len(rows)
                bytes_used += len(json.dumps(rows, ensure_ascii=False, default=str).encode())

            elapsed_ms = int((time.perf_counter() - script_started) * 1000)
            conn.execute("ROLLBACK")
            last = next((s for s in reversed(statements) if s["columns"]), None)
            return SandboxResult(
                success=True,
                columns=last["columns"] if last else [],
                column_types=last["column_types"] if last else [],
                rows=last["rows"] if last else [],
                row_count=last["row_count"] if last else 0,
                execution_time_ms=elapsed_ms,
                statements=statements,
                mode="read_only",
                rolled_back=True,
            )
        except psycopg.Error as exc:
            error_type, message = _classify_error(exc, self._timeout_ms)
            return SandboxResult(
                success=False, error_type=error_type, error_message=message,
                statements=statements,
                execution_time_ms=int((time.perf_counter() - script_started) * 1000),
            )
        finally:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            conn.close()

    def _execute_write_bounded(self, conn, canonical: str, row_budget: int):
        """Execute one DDL/DML statement, optionally bounding RETURNING rows."""
        with conn.cursor() as cur:
            cur.execute(canonical)
            if cur.description is None:
                return [], [], [], max(0, cur.rowcount)
            columns = [d.name for d in cur.description]
            rows = cur.fetchmany(max(1, row_budget + 1))
            if len(rows) > row_budget:
                return None
            return (columns,
                    ["number" if d.type_code in {20, 21, 23, 700, 701, 1700}
                     else "boolean" if d.type_code == 16 else "text" for d in cur.description],
                    [[_jsonable(value) for value in row] for row in rows],
                    len(rows))

    def execute_writable_script(self, sql_text: str, *, schema: Optional[str] = None,
                                capture_tables: Optional[list[str]] = None) -> SandboxResult:
        """Demo-only DDL/DML/SELECT script in a disposable, rolled-back transaction.

        ``capture_tables`` records the committed state of those tables before
        the transaction is rolled back; DML grading uses it to compare the
        learner's mutation with the reference mutation.
        """
        sql_text = (sql_text or "").strip()
        if len(sql_text.encode()) > self._max_sql_bytes:
            return SandboxResult(False, error_type="query_too_large",
                                 error_message="SQL exceeds the input limit")
        issue = validate_writable_script(
            sql_text,
            allowed_schemas=frozenset({schema}) if schema else frozenset(),
            max_statements=self._max_statements,
        )
        if issue:
            return SandboxResult(False, error_type=issue[0], error_message=issue[1],
                                 error_statement_index=issue[2])
        try:
            conn = self._connect(self._writable_url, autocommit=True)
        except (psycopg.OperationalError, OSError):
            return SandboxResult(False, error_type="sandbox_unavailable",
                                 error_message="The SQL sandbox is unavailable")
        statements: list[dict] = []
        rows_used = bytes_used = 0
        started = time.perf_counter()
        try:
            conn.execute(f"SET statement_timeout = {self._timeout_ms}")
            conn.execute(f"SET idle_in_transaction_session_timeout = {self._timeout_ms * 4}")
            if schema:
                conn.execute(pgsql.SQL("SET search_path TO {}").format(pgsql.Identifier(schema)))
            conn.execute("BEGIN")
            classification = classify_script(sql_text, max_statements=self._max_statements)
            if not classification.ok:
                return SandboxResult(False, error_type=classification.error_type,
                                     error_message=classification.error_message)
            for stmt in classification.statements:
                elapsed = (time.perf_counter() - started) * 1000
                if elapsed > self._max_script_ms:
                    return SandboxResult(False, error_type="timeout",
                                         error_message="Script exceeded the execution time limit",
                                         statements=statements, error_statement_index=stmt.index,
                                         execution_time_ms=int(elapsed))
                timeout_ms = min(self._timeout_ms, max(1, int(self._max_script_ms - elapsed)))
                conn.execute(f"SET LOCAL statement_timeout = {timeout_ms}")
                canonical = stmt.sql.rstrip().rstrip(";")
                stmt_started = time.perf_counter()
                columns, column_types, rows, row_count = [], [], [], 0
                err_type = err_msg = None
                try:
                    if stmt.kind == "read_only":
                        columns, column_types, rows, err_type, err_msg = self._read_bounded(
                            conn, canonical, timeout_ms, started,
                            max(0, self._max_rows_script - rows_used),
                            max(0, self._max_bytes_script - bytes_used),
                        )
                        row_count = len(rows)
                    else:
                        bounded = self._execute_write_bounded(
                            conn, canonical, max(0, self._max_rows_script - rows_used))
                        if bounded is None:
                            return SandboxResult(False, error_type="result_too_large",
                                                 error_message="Result exceeds the row limit",
                                                 statements=statements, error_statement_index=stmt.index)
                        columns, column_types, rows, row_count = bounded
                except psycopg.Error as exc:
                    err_type, err_msg = _classify_error(exc, timeout_ms)
                entry = {
                    "index": stmt.index, "kind": stmt.kind,
                    "command": canonical.split(None, 1)[0].upper() if canonical else "",
                    "row_count": row_count, "columns": columns,
                    "column_types": column_types, "rows": rows,
                    "execution_time_ms": int((time.perf_counter() - stmt_started) * 1000),
                }
                if err_type:
                    entry.update(error_type=err_type, error_message=err_msg)
                    statements.append(entry)
                    return SandboxResult(False, error_type=err_type, error_message=err_msg,
                                         statements=statements, error_statement_index=stmt.index,
                                         execution_time_ms=int((time.perf_counter() - started) * 1000))
                statements.append(entry)
                rows_used += len(rows)
                bytes_used += len(json.dumps(rows, ensure_ascii=False, default=str).encode())
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            table_states = self._capture_table_states(conn, capture_tables or [])
            conn.execute("ROLLBACK")
            last = next((s for s in reversed(statements) if s["columns"]), None)
            return SandboxResult(
                success=True,
                columns=last["columns"] if last else [],
                column_types=last["column_types"] if last else [],
                rows=last["rows"] if last else [],
                row_count=last["row_count"] if last else 0,
                execution_time_ms=elapsed_ms, statements=statements,
                mode="writable", rolled_back=True, table_states=table_states,
            )
        except psycopg.Error as exc:
            error_type, message = _classify_error(exc, self._timeout_ms)
            return SandboxResult(False, error_type=error_type, error_message=message,
                                 statements=statements,
                                 execution_time_ms=int((time.perf_counter() - started) * 1000))
        finally:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            conn.close()

    @staticmethod
    def _capture_table_states(conn, tables: list[str]) -> list[dict]:
        states = []
        for table in tables:
            try:
                cursor = conn.execute(
                    pgsql.SQL("SELECT * FROM {}").format(pgsql.Identifier(table))
                )
                columns = [column.name for column in (cursor.description or [])]
                rows = [[_jsonable(value) for value in row] for row in cursor.fetchall()]
                rows.sort(key=lambda row: json.dumps(row, sort_keys=True, default=str))
                states.append({"table": table, "columns": columns, "rows": rows})
            except psycopg.errors.UndefinedTable:
                states.append({"table": table, "missing": True})
        return states

    # ---------- dataset provisioning ----------

    def provision_dataset(self, setup_sql: str) -> str:
        """Create a fresh dataset schema and load ``setup_sql`` into it.

        Setup is validated before connecting, then executed only after SET ROLE
        to a non-login, non-superuser dataset owner inside a timed transaction.
        The administrative connection creates/drops the isolated schema only.
        """
        schema = f"{DATASET_SCHEMA_PREFIX}{uuid.uuid4().hex[:12]}"
        try:
            statements = validated_setup_statements(setup_sql, self._max_setup_bytes)
        except ValueError as exc:
            raise SandboxError("dataset_setup_failed", str(exc)) from None
        try:
            with self._connect(
                self._admin_url,
                autocommit=True,
            ) as conn:
                # Repeatable bootstrap for existing sandbox volumes. No
                # generated statement ever executes before the role switch.
                conn.execute("""DO $$ BEGIN
                  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='dbcas_dataset_setup') THEN
                    CREATE ROLE dbcas_dataset_setup NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
                  END IF;
                EXCEPTION WHEN duplicate_object OR unique_violation THEN NULL; END $$""")
                with conn.transaction():
                    conn.execute(f"SET LOCAL statement_timeout = {self._timeout_ms}")
                    conn.execute(pgsql.SQL("CREATE SCHEMA {} AUTHORIZATION dbcas_dataset_setup").format(pgsql.Identifier(schema)))
                    conn.execute("SET LOCAL ROLE dbcas_dataset_setup")
                    conn.execute(pgsql.SQL("SET LOCAL search_path TO {}").format(pgsql.Identifier(schema)))
                    conn.execute(pgsql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT SELECT ON TABLES TO {}").format(pgsql.Identifier(schema),pgsql.Identifier(self._learner_role)))
                    conn.execute(pgsql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(pgsql.Identifier(schema),pgsql.Identifier(self._learner_role)))
                    if self._writable:
                        conn.execute(pgsql.SQL("GRANT USAGE, CREATE ON SCHEMA {} TO learner_rw").format(pgsql.Identifier(schema)))
                        conn.execute(pgsql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {} TO learner_rw").format(pgsql.Identifier(schema)))
                        conn.execute(pgsql.SQL("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {} TO learner_rw").format(pgsql.Identifier(schema)))
                        conn.execute(pgsql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT ALL ON TABLES TO learner_rw").format(pgsql.Identifier(schema)))
                        conn.execute(pgsql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT ALL ON SEQUENCES TO learner_rw").format(pgsql.Identifier(schema)))
                    for statement in statements:
                        conn.execute(statement)
                    if self._writable:
                        conn.execute(pgsql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {} TO learner_rw").format(pgsql.Identifier(schema)))
                        conn.execute(pgsql.SQL("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {} TO learner_rw").format(pgsql.Identifier(schema)))
        except (psycopg.OperationalError, OSError) as exc:
            logger.warning("sandbox admin connect failed: %s", type(exc).__name__)
            raise SandboxError("sandbox_unavailable", "The SQL sandbox is unavailable")
        except psycopg.Error as exc:
            logger.warning("dataset provisioning failed: %s", type(exc).__name__)
            self.drop_dataset(schema)
            raise SandboxError(
                "dataset_setup_failed", "Could not prepare the SQL test dataset"
            )
        return schema

    def drop_dataset(self, schema: str) -> None:
        """Drop a dataset schema and everything in it. Best-effort."""
        if not schema or not schema.startswith(DATASET_SCHEMA_PREFIX):
            return
        try:
            with self._connect(
                self._admin_url,
                autocommit=True,
            ) as conn:
                conn.execute(
                    pgsql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        pgsql.Identifier(schema)
                    )
                )
        except Exception as exc:  # noqa: BLE001 - cleanup must never break callers
            logger.warning("drop_dataset(%s) failed: %s", schema, type(exc).__name__)

    def cleanup_datasets(self) -> int:
        """Drop every leftover ``ds_*`` schema. Returns the number dropped."""
        dropped = 0
        try:
            with self._connect(
                self._admin_url,
                autocommit=True,
            ) as conn:
                rows = conn.execute(
                    "SELECT nspname FROM pg_namespace WHERE nspname LIKE %s",
                    (f"{DATASET_SCHEMA_PREFIX}%",),
                ).fetchall()
                for (name,) in rows:
                    conn.execute(
                        pgsql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                            pgsql.Identifier(name)
                        )
                    )
                    dropped += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("cleanup_datasets failed: %s", type(exc).__name__)
        return dropped

    # ---------- health ----------

    def health_check(self) -> bool:
        """True when the sandbox accepts a trivial read-only learner query."""
        try:
            with self._connect(
                self._learner_url,
                autocommit=True,
            ) as conn:
                return conn.execute("SELECT 1").fetchone() == (1,)
        except Exception:  # noqa: BLE001
            return False

    def validate_environment(self) -> list[str]:
        """Verify the sandbox isolation guarantees; returns a list of problems.

        An empty list means: learner role exists and is not superuser, the
        statement timeout is effective, and the admin connection works.
        """
        problems: list[str] = []
        try:
            with self._connect(
                self._learner_url,
                autocommit=True,
            ) as conn:
                user, is_super = conn.execute(
                    "SELECT current_user, rolsuper FROM pg_roles "
                    "WHERE rolname = current_user"
                ).fetchone()
                if user != self._learner_role:
                    problems.append(f"learner connection maps to unexpected role {user!r}")
                if is_super:
                    problems.append("learner role is a superuser")
                timeout_ms = conn.execute("SHOW statement_timeout").fetchone()[0]
                if not self._timeout_within_budget(timeout_ms):
                    problems.append(
                        f"statement_timeout is {timeout_ms}, expected <= {self._timeout_ms}ms"
                    )
                read_only = conn.execute(
                    "SHOW default_transaction_read_only"
                ).fetchone()[0]
                if str(read_only).lower() != "on":
                    problems.append("learner role is not default_transaction_read_only")
        except Exception as exc:  # noqa: BLE001
            problems.append(f"learner connection failed ({type(exc).__name__})")
        try:
            with self._connect(
                self._admin_url,
                autocommit=True,
            ) as conn:
                version = conn.execute("SHOW server_version_num").fetchone()[0]
                if int(version) < 170000:
                    problems.append(f"sandbox runs PostgreSQL {version}, expected 17")
        except Exception as exc:  # noqa: BLE001
            problems.append(f"admin connection failed ({type(exc).__name__})")
        return problems

    def _timeout_within_budget(self, setting: str) -> bool:
        try:
            raw = str(setting).strip().lower()
            if raw.endswith("ms"):
                value = float(raw[:-2])
            elif raw.endswith("s"):
                value = float(raw[:-1]) * 1000
            elif raw.endswith("min"):
                value = float(raw[:-3]) * 60000
            else:
                value = float(raw)
            return 0 < value <= self._timeout_ms
        except ValueError:
            return False


def build_sandbox_runner(settings):
    """Select the deployment's executor without changing legacy shared fixtures."""
    if settings.sandbox_mode == "ephemeral":
        from .ephemeral_sandbox import EphemeralSandboxRunner
        return EphemeralSandboxRunner(settings)
    return SandboxRunner(settings)
