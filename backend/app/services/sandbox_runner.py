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
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import psycopg
from psycopg import sql as pgsql

from ..config import Settings
from .sql_validator import validate_learner_sql

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
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: int = 0
    error_type: Optional[str] = None
    error_message: Optional[str] = None


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
        self._admin_url = settings.sandbox_admin_url
        self._learner_role = settings.sandbox_learner_role
        self._timeout_ms = settings.sandbox_statement_timeout_ms
        self._max_rows = settings.sandbox_max_rows
        self._max_sql_bytes = settings.sandbox_max_sql_bytes
        self._connect_timeout = settings.sandbox_connect_timeout_seconds

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
            conn = psycopg.connect(
                self._learner_url,
                autocommit=True,
                connect_timeout=self._connect_timeout,
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
            cur = conn.execute(sql_text)
            columns = [d.name for d in cur.description] if cur.description else []
            fetched = cur.fetchmany(self._max_rows + 1) if cur.description else []
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            conn.execute("ROLLBACK")

            if len(fetched) > self._max_rows:
                return SandboxResult(
                    success=False,
                    columns=columns,
                    execution_time_ms=elapsed_ms,
                    error_type="result_too_large",
                    error_message=f"Result exceeds the {self._max_rows}-row limit",
                )
            rows = [[_jsonable(v) for v in row] for row in fetched]
            return SandboxResult(
                success=True,
                columns=columns,
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

    # ---------- dataset provisioning ----------

    def provision_dataset(self, setup_sql: str) -> str:
        """Create a fresh dataset schema and load ``setup_sql`` into it.

        Returns the schema name the dataset lives in; the caller must later
        call :meth:`drop_dataset`. Runs on the admin connection — setup SQL is
        administrator-authored trusted DDL+seed, not learner input.
        """
        schema = f"{DATASET_SCHEMA_PREFIX}{uuid.uuid4().hex[:12]}"
        try:
            with psycopg.connect(
                self._admin_url,
                autocommit=True,
                connect_timeout=self._connect_timeout,
            ) as conn:
                conn.execute(
                    pgsql.SQL("CREATE SCHEMA {}").format(pgsql.Identifier(schema))
                )
                conn.execute(
                    pgsql.SQL(
                        "ALTER DEFAULT PRIVILEGES IN SCHEMA {} "
                        "GRANT SELECT ON TABLES TO {}"
                    ).format(
                        pgsql.Identifier(schema),
                        pgsql.Identifier(self._learner_role),
                    )
                )
                conn.execute(
                    pgsql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                        pgsql.Identifier(schema),
                        pgsql.Identifier(self._learner_role),
                    )
                )
                conn.execute(
                    pgsql.SQL("SET search_path TO {}").format(
                        pgsql.Identifier(schema)
                    )
                )
                conn.execute(setup_sql)
        except (psycopg.OperationalError, OSError) as exc:
            logger.warning("sandbox admin connect failed: %s", type(exc).__name__)
            raise SandboxError("sandbox_unavailable", "The SQL sandbox is unavailable")
        except psycopg.Error as exc:
            logger.warning("dataset provisioning failed: %s", exc.diag.message_primary)
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
            with psycopg.connect(
                self._admin_url,
                autocommit=True,
                connect_timeout=self._connect_timeout,
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
            with psycopg.connect(
                self._admin_url,
                autocommit=True,
                connect_timeout=self._connect_timeout,
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
            with psycopg.connect(
                self._learner_url,
                autocommit=True,
                connect_timeout=self._connect_timeout,
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
            with psycopg.connect(
                self._learner_url,
                autocommit=True,
                connect_timeout=self._connect_timeout,
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
            with psycopg.connect(
                self._admin_url,
                autocommit=True,
                connect_timeout=self._connect_timeout,
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
