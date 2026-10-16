"""Validate dataset DDL/seed before any SQL reaches a provisioning connection."""
import re

import sqlglot
from sqlglot import exp

from .sql_validator import validate_learner_sql


def validated_setup_statements(sql_text: str, max_bytes: int = 65536) -> list[str]:
    if not isinstance(sql_text, str) or not sql_text.strip() or len(sql_text.encode()) > max_bytes:
        raise ValueError("Dataset setup must be nonempty and within the setup byte limit")
    try:
        statements = [s for s in sqlglot.parse(sql_text, read="postgres") if s is not None]
    except Exception:
        raise ValueError("Dataset setup contains invalid PostgreSQL SQL") from None
    if not 1 <= len(statements) <= 64:
        raise ValueError("Dataset setup supports at most 64 statements")
    declared = set()
    output = []
    for stmt in statements:
        if isinstance(stmt, exp.Create):
            kind = (stmt.args.get("kind") or "").upper()
            if kind == "TABLE" and isinstance(stmt.this, exp.Schema) and not stmt.args.get("expression"):
                table = stmt.this.this
            elif kind == "VIEW" and isinstance(stmt.this, exp.Table):
                table = stmt.this
                query = stmt.args.get("expression")
                if query is None or validate_learner_sql(query.sql(dialect="postgres")):
                    raise ValueError("Dataset views must contain safe read-only SELECT queries")
            else:
                raise ValueError("Dataset setup allows only explicit CREATE TABLE and safe CREATE VIEW")
            if stmt.args.get("properties") or stmt.args.get("replace"):
                raise ValueError("Dataset setup cannot replace objects or change storage properties")
            if table.db or table.catalog or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", table.name):
                raise ValueError("Dataset objects must use unqualified local identifiers")
            if table.name.lower().startswith(("pg_", "sql_")):
                raise ValueError("Dataset objects cannot use reserved catalog names")
            declared.add(table.name.lower())
        elif isinstance(stmt, exp.Insert):
            values = stmt.args.get("expression")
            if not isinstance(values, exp.Values) or len(values.expressions) > 4096:
                raise ValueError("Dataset seeds must use bounded literal INSERT VALUES")
        else:
            raise ValueError("Dataset setup permits CREATE TABLE/VIEW and literal INSERT only")
        for table in stmt.find_all(exp.Table):
            if table.db or table.catalog or table.name.lower() not in declared:
                raise ValueError("Dataset setup cannot reference other schemas or undeclared tables")
        # Data/rubric fixtures are deterministic. No callable defaults, query
        # strings, external functions, or programmable objects are necessary.
        if isinstance(stmt, exp.Insert) and any(isinstance(n, (exp.Func, exp.Select, exp.Subquery)) for n in stmt.walk()):
            raise ValueError("Dataset INSERT values cannot execute functions or queries")
        if isinstance(stmt, exp.Create) and (stmt.args.get("kind") or "").upper() == "TABLE":
            if any(isinstance(n, exp.Func) for n in stmt.walk()):
                raise ValueError("Dataset table definitions cannot execute functions")
        output.append(stmt.sql(dialect="postgres"))
    return output
