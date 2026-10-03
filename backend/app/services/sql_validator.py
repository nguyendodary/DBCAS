"""Learner SQL validation — the parser layer of sandbox safety (QA03, NFR-02).

A learner statement is acceptable iff it is a *single* read-only
SELECT-family query (SELECT / WITH / set operations / subqueries / VALUES —
the academic scope of the assessment). Everything else — DML, DDL, multi
statements, locking reads, system catalogs, dangerous functions — is rejected
*before* a database connection is opened, so the read-only role and rolled
back transaction remain a second line of defense rather than the only one.

``validate_learner_sql`` returns ``None`` when the statement is acceptable or
an ``(error_type, learner_safe_message)`` tuple. Messages never echo server
internals; they only describe the rejected construct in the learner's own
input.
"""

from typing import Optional

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError, TokenError

# Root node types that produce a read-only result set.
_ALLOWED_ROOTS = (
    exp.Select,
    exp.Union,
    exp.Intersect,
    exp.Except,
    exp.Subquery,
    exp.Values,
)

# Node types that must not appear anywhere inside the statement — covers
# DML/DDL wrapped in CTEs or subqueries as well as top-level commands.
_FORBIDDEN_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.TruncateTable,
    exp.Command,  # EXPLAIN / COPY / VACUUM / CALL / DO / GRANT / SET / …
    exp.Transaction,  # BEGIN / COMMIT / ROLLBACK / START TRANSACTION
    exp.Set,
    exp.Copy,
    exp.Pragma,
    exp.Describe,
    exp.Analyze,
    exp.Cache,
    exp.Uncache,
    exp.Grant,
    exp.Revoke,
    exp.Into,  # SELECT … INTO writes a new table
    exp.Lock,  # FOR UPDATE / FOR SHARE / FOR NO KEY UPDATE / FOR KEY SHARE
    exp.UserDefinedFunction,
)

# Schemas a learner query may never reference explicitly. Unqualified names
# resolve through search_path; qualified catalog names are blocked outright.
_FORBIDDEN_SCHEMAS = {"pg_catalog", "pg_toast", "information_schema"}

# Catalog objects expose cluster/session internals (pg_stat_activity shows
# other sessions' queries, pg_settings exposes server configuration).
_FORBIDDEN_NAME_PREFIXES = ("pg_", "sql_")

# Functions with side effects, privilege surface, or that disclose server
# internals (paths, addresses, configuration). Prefixes catch whole families
# (pg_ls_*, pg_read_*, dblink_*, lo_*).
_UNSAFE_FUNCTIONS = {
    "pg_sleep",
    "pg_notify",
    "pg_advisory_lock",
    "pg_advisory_unlock",
    "pg_advisory_unlock_all",
    "pg_terminate_backend",
    "pg_cancel_backend",
    "pg_reload_conf",
    "pg_backend_pid",
    "pg_postmaster_start_time",
    "pg_conf_load_time",
    "set_config",
    "current_setting",
    "nextval",
    "setval",
    "inet_server_addr",
    "inet_server_port",
    "inet_client_addr",
    "inet_client_port",
    "txid_current",
    "pg_current_xact_id",
    "pg_is_in_recovery",
}
_UNSAFE_FUNCTION_PREFIXES = (
    "pg_ls_",
    "pg_read_",
    "pg_write_",
    "pg_stat_get",
    "pg_terminate",
    "dblink",
    "lo_",
    "xml_",
)


def _qualifier_error(db: str, catalog: str, allowed: set[str]) -> Optional[str]:
    catalog = (catalog or "").lower()
    db = (db or "").lower()
    if catalog:
        return "cross-database references are not allowed"
    if db in _FORBIDDEN_SCHEMAS or db.startswith("pg_"):
        return "system catalogs are not accessible in the sandbox"
    if db and db not in allowed:
        return f"schema {db!r} is not accessible in the sandbox"
    return None


def validate_learner_sql(
    sql_text: str, *, allowed_schemas: frozenset[str] = frozenset()
) -> Optional[tuple[str, str]]:
    """Statically validate one learner statement for sandbox execution.

    ``allowed_schemas`` are extra schema qualifiers permitted in addition to
    ``public`` (the runner passes the provisioned dataset schema). Unqualified
    table names are always allowed — they resolve via search_path.
    """
    # Reject NUL/control characters that can smuggle odd encodings past a
    # parser (whitespace \t \n \r and the space stay fine, of course).
    if any(ord(c) < 32 and c not in "\t\n\r" for c in sql_text):
        return "invalid_input", "The query contains unsupported control characters"

    try:
        statements = [e for e in sqlglot.parse(sql_text, read="postgres") if e]
    except (ParseError, TokenError) as exc:
        return "syntax_error", f"Could not parse the SQL statement ({exc})"
    except Exception:  # noqa: BLE001 — parser must never take the request down
        return "syntax_error", "Could not parse the SQL statement"

    if not statements:
        return "empty_query", "The query is empty"
    if len(statements) > 1:
        return "multiple_statements", "Only a single SELECT statement is allowed"

    expr = statements[0]
    if not isinstance(expr, _ALLOWED_ROOTS):
        return (
            "not_a_select",
            "Only a single read-only SELECT query is allowed in the sandbox",
        )

    allowed = {"public"} | set(allowed_schemas)
    for node in expr.walk():
        if isinstance(node, _FORBIDDEN_NODES):
            kind = type(node).__name__.lower()
            return (
                "prohibited_statement",
                f"{kind} constructs are not allowed in learner queries",
            )
        if isinstance(node, exp.Table):
            name = (node.name or "").lower()
            if name.startswith(_FORBIDDEN_NAME_PREFIXES) and not node.db:
                return (
                    "forbidden_schema",
                    "system catalogs are not accessible in the sandbox",
                )
            issue = _qualifier_error(node.db or "", node.catalog or "", allowed)
            if issue:
                return "forbidden_schema", issue
        if isinstance(node, exp.Column):
            issue = _qualifier_error(node.db or "", node.catalog or "", allowed)
            if issue:
                return "forbidden_schema", issue
        if isinstance(node, exp.Func):
            # sqlglot normalizes the schema qualifier away
            # (pg_catalog.pg_sleep → pg_sleep), so the name check is enough.
            if isinstance(node, exp.Anonymous):
                fname = str(node.name or "").lower()
            else:
                fname = str(node.sql_name() or "").lower()
            if fname in _UNSAFE_FUNCTIONS or fname.startswith(
                _UNSAFE_FUNCTION_PREFIXES
            ):
                return (
                    "unsafe_function",
                    f"function {fname}() is not allowed in learner queries",
                )
    return None
