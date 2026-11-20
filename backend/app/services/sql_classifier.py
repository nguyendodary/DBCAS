"""AST-based learner SQL classification and script policy (SQL sandbox).

This is the *policy* layer of sandbox safety. It uses libpg_query (via
``pglast``) — the same PostgreSQL parser the server itself uses — instead of
regex or string matching, so comments, dollar quoting, nested CTEs and
statement boundaries are resolved exactly as PostgreSQL resolves them.

Two layers are kept independent on purpose:

* this module decides whether a script is *syntactically and by policy*
  acceptable before any connection is opened (default deny / fail closed);
* the database role and its grants remain the second line of defence.

``validate_learner_sql`` in :mod:`sql_validator` is deliberately left
unchanged: while the multi-statement flag is off, the legacy single-SELECT
path keeps its exact, byte-identical behavior.
"""

from dataclasses import dataclass
from typing import Optional

from pglast import ast, parse_sql
from pglast.parser import ParseError
from pglast.visitors import Visitor

# Typed classification outcomes. Writable kinds are classified (so callers can
# render an accurate mode badge) but are rejected by the read-only policy.
READ_ONLY = "read_only"
WRITE_DML = "write_dml"
DDL = "ddl"
FORBIDDEN = "forbidden"

# Root statement node types (libpg_query / PostgreSQL 17 AST names).
_ROOT_READ_ONLY = frozenset({"SelectStmt"})  # SELECT, VALUES, set ops, WITH
_ROOT_WRITE_DML = frozenset({"InsertStmt", "UpdateStmt", "DeleteStmt", "MergeStmt"})
_ROOT_DDL = frozenset({
    "CreateStmt", "ViewStmt", "IndexStmt", "AlterTableStmt", "DropStmt",
    "TruncateStmt", "RenameStmt", "AlterObjectSchemaStmt", "AlterOwnerStmt",
    "CreateTableAsStmt", "RefreshMatViewStmt", "CreateSchemaStmt",
    "CreateSeqStmt", "AlterSeqStmt", "CompositeTypeStmt", "CreateEnumStmt",
    "CreateDomainStmt", "DefineStmt", "CommentStmt",
})

# Any node whose type ends in "Stmt" other than the read-only set is a
# statement-level construct that the read-only policy does not allow. This is
# an allow-list by shape, so a new/unknown statement type fails closed.
_ALLOWED_NESTED_STMT_NODES = frozenset({"SelectStmt"})

# Non-Stmt nodes that must never appear in a read-only learner script.
_FORBIDDEN_NODES = frozenset({
    "IntoClause",       # SELECT ... INTO (creates a table)
    "LockingClause",    # SELECT ... FOR UPDATE / SHARE / KEY SHARE
    "CopyStmt",
    "DoStmt",
})

# Catalog/session internals and cross-database qualifiers are never allowed.
_FORBIDDEN_SCHEMAS = frozenset({"pg_catalog", "pg_toast", "information_schema", "pg_temp"})
_FORBIDDEN_NAME_PREFIXES = ("pg_", "sql_", "pg_temp")

# Side-effecting / information-disclosing functions. The prefix family denies
# the whole pg_*, dblink*, lo_*, xml_* surface, matching the legacy deny-list.
_UNSAFE_FUNCTIONS = frozenset({
    "pg_sleep", "pg_notify", "pg_advisory_lock", "pg_advisory_unlock",
    "pg_advisory_unlock_all", "pg_terminate_backend", "pg_cancel_backend",
    "pg_reload_conf", "pg_backend_pid", "set_config", "current_setting",
    "nextval", "setval", "currval", "lastval", "query_to_xml",
    "table_to_xml", "schema_to_xml", "database_to_xml", "xpath",
})
_UNSAFE_FUNCTION_PREFIXES = (
    "pg_", "dblink", "lo_", "xml_", "query_to_", "table_to_",
    "schema_to_", "database_to_", "cursor_to_",
)

# Non-deterministic functions are permitted in practice but normalized by the
# (trusted) grader; they are listed here so the policy can report them.
NONDETERMINISTIC_FUNCTIONS = frozenset({"now", "random", "current_timestamp", "clock_timestamp"})


@dataclass(frozen=True)
class StatementClass:
    """One parsed statement and its policy classification."""

    index: int                 # 1-based for learner-facing messages
    kind: str                  # READ_ONLY / WRITE_DML / DDL / FORBIDDEN
    node_type: str
    sql: str                   # exact original slice, comments excluded


@dataclass(frozen=True)
class ScriptClassification:
    """Result of parsing and classifying a whole script (fail closed)."""

    statements: tuple[StatementClass, ...] = ()
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_index: Optional[int] = None

    @property
    def ok(self) -> bool:
        return self.error_type is None


def _has_control_chars(text: str) -> bool:
    return any(ord(c) < 32 and c not in "\t\n\r" for c in text)


def _name_of(node) -> str:
    """String value of a pglast String node (or a plain value)."""
    return str(getattr(node, "sval", node) or "")


class _NodeScanner(Visitor):
    """Collect every node type and the concrete objects the policy inspects."""

    def __init__(self):
        self.node_types: set[str] = set()
        self.range_vars: list = []
        self.type_names: list = []
        self.func_calls: list = []

    def visit(self, ancestors, node):
        self.node_types.add(type(node).__name__)
        if isinstance(node, ast.RangeVar):
            self.range_vars.append(node)
        elif isinstance(node, ast.TypeName):
            self.type_names.append(node)
        elif isinstance(node, ast.FuncCall):
            self.func_calls.append(node)
        # Returning None means Continue in pglast; a truthy return skips children.


def _scan(expr) -> _NodeScanner:
    scanner = _NodeScanner()
    scanner(expr)
    return scanner


def _qualifier_issue(schema: str, catalog: str, allowed: frozenset[str]) -> Optional[str]:
    schema = (schema or "").lower()
    catalog = (catalog or "").lower()
    if catalog:
        return "cross-database references are not allowed"
    if schema in _FORBIDDEN_SCHEMAS or schema.startswith(_FORBIDDEN_NAME_PREFIXES):
        return "system catalogs are not accessible in the sandbox"
    if schema and schema not in allowed:
        return f"schema {schema!r} is not accessible in the sandbox"
    return None


def _classify_root(node) -> str:
    name = type(node).__name__
    if name in _ROOT_READ_ONLY:
        return READ_ONLY
    if name in _ROOT_WRITE_DML:
        return WRITE_DML
    if name in _ROOT_DDL:
        return DDL
    return FORBIDDEN


def classify_script(sql_text: str, *, max_statements: int = 32) -> ScriptClassification:
    """Parse the full script and return a typed classification per statement.

    Fails closed: a parse error, empty input, too many statements, or an
    unrecognized root statement yields an error instead of a partial result.
    """
    sql_text = sql_text or ""
    if _has_control_chars(sql_text):
        return ScriptClassification(error_type="invalid_input",
                                    error_message="The query contains unsupported control characters")
    if not sql_text.strip():
        return ScriptClassification(error_type="empty_query", error_message="The query is empty")
    if len(sql_text.encode("utf-8")) > 100_000:
        return ScriptClassification(error_type="query_too_large",
                                    error_message="SQL exceeds the parser input limit")
    try:
        raw = parse_sql(sql_text)
    except ParseError as exc:
        return ScriptClassification(error_type="syntax_error",
                                    error_message="Could not parse the SQL statement")
    except Exception:  # noqa: BLE001 - the parser must never take a request down
        return ScriptClassification(error_type="syntax_error",
                                    error_message="Could not parse the SQL statement")
    if not raw:
        return ScriptClassification(error_type="empty_query", error_message="The query is empty")
    if len(raw) > max_statements:
        return ScriptClassification(error_type="too_many_statements",
                                    error_message=f"At most {max_statements} statements are allowed")

    statements: list[StatementClass] = []
    for index, stmt in enumerate(raw, start=1):
        start = stmt.stmt_location or 0
        end = start + (stmt.stmt_len or 0)
        text = sql_text[start:end].strip() if stmt.stmt_len else sql_text[start:].strip()
        statements.append(StatementClass(
            index=index,
            kind=_classify_root(stmt.stmt),
            node_type=type(stmt.stmt).__name__,
            sql=text,
        ))
    return ScriptClassification(statements=tuple(statements))


def validate_read_only_script(
    sql_text: str,
    *,
    allowed_schemas: frozenset[str] = frozenset(),
    max_statements: int = 32,
) -> Optional[tuple[str, str, Optional[int]]]:
    """Validate a multi-statement *read-only* script.

    Returns ``None`` when every statement is acceptable, otherwise
    ``(error_type, learner_safe_message, statement_index)``. This is used only
    by the opt-in multi-statement path; the legacy validator is untouched.
    """
    classification = classify_script(sql_text, max_statements=max_statements)
    if not classification.ok:
        return (classification.error_type, classification.error_message, classification.error_index)

    allowed = frozenset({"public"}) | frozenset(allowed_schemas)
    for statement in classification.statements:
        try:
            expr = parse_sql(statement.sql)[0].stmt
        except Exception:  # noqa: BLE001 - already parsed once; still fail closed
            return ("syntax_error", "Could not parse the SQL statement", statement.index)
        scanner = _scan(expr)

        # 1. Statement kind must be read-only.
        if statement.kind != READ_ONLY:
            if statement.kind == WRITE_DML:
                return ("prohibited_statement",
                        "Data-modifying statements are not allowed in read-only mode",
                        statement.index)
            if statement.kind == DDL:
                return ("prohibited_statement",
                        "Schema-changing statements are not allowed in read-only mode",
                        statement.index)
            return ("prohibited_statement",
                    "This statement is not allowed in the sandbox",
                    statement.index)

        # 2. Reject any statement-level or DML/DDL node anywhere (CTEs included).
        forbidden_types = (
            _ROOT_WRITE_DML | _ROOT_DDL
            | {"TransactionStmt", "VariableSetStmt", "VariableShowStmt",
               "VariableResetStmt", "GrantStmt", "RevokeStmt", "LockStmt",
               "ExplainStmt", "CallStmt", "CreateFunctionStmt", "AlterSystemStmt",
               "CreateExtensionStmt", "CreateRoleStmt", "PrepareStmt",
               "ExecuteStmt", "DeclareCursorStmt", "FetchStmt", "ListenStmt",
               "NotifyStmt", "DiscardStmt", "VacuumStmt", "CheckPointStmt"}
            | _FORBIDDEN_NODES
            | {"IntoClause", "LockingClause"}
        )
        for node_type in scanner.node_types:
            if node_type in forbidden_types:
                return ("prohibited_statement",
                        f"{node_type} constructs are not allowed in learner queries",
                        statement.index)
            if node_type != "SelectStmt" and node_type.endswith("Stmt"):
                # Unknown statement node — fail closed.
                return ("prohibited_statement",
                        f"{node_type} constructs are not allowed in learner queries",
                        statement.index)

        # 3. Schema and name qualifiers.
        for var in scanner.range_vars:
            issue = _qualifier_issue(var.schemaname or "", var.catalogname or "", allowed)
            if issue:
                return ("forbidden_schema", issue, statement.index)
            name = (_name_of(var.relname) if var.relname else "").lower()
            if name.startswith(_FORBIDDEN_NAME_PREFIXES) and not var.schemaname:
                return ("forbidden_schema",
                        "system catalogs are not accessible in the sandbox", statement.index)

        # 4. Function policy (schema-qualified names are normalized by component).
        for call in scanner.func_calls:
            parts = [_name_of(part).lower() for part in (call.funcname or ())]
            if not parts:
                continue
            fname = parts[-1]
            if any(part in _FORBIDDEN_SCHEMAS or part.startswith(_FORBIDDEN_NAME_PREFIXES)
                   for part in parts[:-1]):
                return ("unsafe_function",
                        f"function {fname}() is not allowed in learner queries", statement.index)
            if fname in _UNSAFE_FUNCTIONS or fname.startswith(_UNSAFE_FUNCTION_PREFIXES):
                return ("unsafe_function",
                        f"function {fname}() is not allowed in learner queries", statement.index)

    return None


__all__ = [
    "READ_ONLY", "WRITE_DML", "DDL", "FORBIDDEN", "NONDETERMINISTIC_FUNCTIONS",
    "StatementClass", "ScriptClassification", "classify_script",
    "validate_read_only_script",
]
