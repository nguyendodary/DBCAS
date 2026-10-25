"""Display literal seed data without executing SQL or exposing grading fixtures."""
from functools import lru_cache

import sqlglot
from sqlglot import exp


def _name(identifier):
    return identifier.name if identifier.args.get("quoted") else identifier.name.lower()


def _value(node):
    if isinstance(node, exp.Null):
        return None
    if isinstance(node, exp.Boolean):
        return bool(node.this)
    if isinstance(node, exp.Literal):
        return node.this
    if isinstance(node, exp.Neg) and isinstance(node.this, exp.Literal) and not node.this.is_string:
        return "-" + node.this.this
    raise ValueError("Seed expression requires database execution")


@lru_cache(maxsize=128)
def dataset_tables(setup_sql):
    """Preview only complete, literal CREATE/INSERT fixtures; otherwise use DDL.

    Never evaluate expressions or invent values for defaults, generated columns,
    UPDATEs, SELECTs or unsupported statements. Preserve quoted identifiers.
    """
    tables = {}
    try:
        for statement in sqlglot.parse(setup_sql or "", read="postgres"):
            if statement is None:
                continue
            if isinstance(statement, exp.Create) and statement.args.get("kind") == "TABLE" and isinstance(statement.this, exp.Schema):
                schema = statement.this
                table = schema.this
                if not isinstance(table, exp.Table) or table.db or table.catalog:
                    return []
                key = _name(table.this)
                if key in tables:
                    return []
                columns = [column for column in schema.expressions if isinstance(column, exp.ColumnDef)]
                if not columns:
                    return []
                tables[key] = {"name": key, "columns": [{"name": _name(c.this), "type": c.args["kind"].sql(dialect="postgres")} for c in columns],
                               "rows": [], "row_count": 0}
            elif isinstance(statement, exp.Insert) and isinstance(statement.expression, exp.Values):
                target = statement.this
                named = isinstance(target, exp.Schema)
                table = target.this if named else target
                if not isinstance(table, exp.Table) or table.db or table.catalog:
                    return []
                data = tables.get(_name(table.this))
                if data is None:
                    return []
                columns = [c["name"] for c in data["columns"]]
                inserted = [_name(c) for c in target.expressions] if named else columns
                # Omitted columns may have defaults: don't guess their values.
                if set(inserted) != set(columns) or len(inserted) != len(columns):
                    return []
                for values in statement.expression.expressions:
                    if len(values.expressions) != len(inserted):
                        return []
                    mapped = dict(zip(inserted, [_value(v) for v in values.expressions]))
                    data["row_count"] += 1
                    if len(data["rows"]) < 100:
                        data["rows"].append([mapped[c] for c in columns])
            else:
                return []
        return list(tables.values())
    except (sqlglot.errors.ParseError, ValueError, KeyError, AttributeError):
        return []
