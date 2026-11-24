"""Semantic comparison between a learner's SQL result and a stored
``sql_test_dataset.expected_result`` (JSONB: expected columns & rows).

Expected-result format::

    {"columns": ["name", ...], "rows": [[v, ...], ...],
     "ordered": false, "check_columns": false}

* ``columns`` — optional; the expected output shape. Its *count* is always
  enforced; names are only enforced when ``check_columns`` is true
  (equivalent formulations with aliases still earn full credit — FR-09).
* ``rows`` — list of row arrays, values as JSON primitives.
* ``ordered`` — optional (default ``false``); when true, row order matters.
* ``check_columns`` — optional (default ``false``); when true the learner's
  column-name set must match ``columns`` (case-insensitive), and rows are
  realigned into expected column order before comparing.

Rows are compared as *multisets* of normalized value tuples: duplicate rows
must appear the same number of times — a plain set would be wrong. Numeric
values compare by value, not representation (``1`` == ``1.0`` == ``1.00``).
"""

from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Optional


@dataclass(frozen=True)
class ExpectedResult:
    columns: Optional[tuple[str, ...]]  # None = "not specified"
    rows: tuple[tuple[Any, ...], ...]
    ordered: bool
    check_columns: bool


@dataclass(frozen=True)
class CompareOutcome:
    status: str  # "passed" | "failed"
    matched: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExpectedTable:
    table: str
    columns: Optional[tuple[str, ...]]
    rows: tuple[tuple[Any, ...], ...]
    missing: bool = False


@dataclass(frozen=True)
class ExpectedState:
    tables: tuple[ExpectedTable, ...]
    ordered: bool


def _norm_value(v: Any) -> Any:
    """Map a JSON value into a comparison-stable primitive.

    Values are type tagged: booleans never compare equal to numbers. Text
    whitespace is meaningful. Numeric wire strings require PostgreSQL metadata.
    """
    if v is None:
        return ("null",)
    if isinstance(v, bool):
        return ("boolean", v)
    if isinstance(v, (int, float, Decimal)):
        try:
            number = Decimal(str(v))
            return ("number", number) if number.is_finite() else ("invalid_number", str(v))
        except InvalidOperation:
            return ("invalid_number", str(v))
    if isinstance(v, str):
        return ("text", v)
    return ("text", str(v))


def _actual_value(value, kind=None):
    if kind == "number" and isinstance(value, str):
        try:
            value = Decimal(value)
        except InvalidOperation:
            return ("invalid_number", value)
    return _norm_value(value)


def _norm_row(row: Any) -> Optional[tuple]:
    if not isinstance(row, (list, tuple)):
        return None
    return tuple(_norm_value(v) for v in row)


def parse_expected(raw: Any) -> Optional[ExpectedResult]:
    """Parse the stored expected_result JSON. Returns None when unusable."""
    if not isinstance(raw, dict):
        return None
    rows_raw = raw.get("rows")
    if not isinstance(rows_raw, list):
        return None
    if any(not isinstance(raw.get(k, False), bool) for k in ("ordered", "check_columns")):
        return None
    rows = []
    for r in rows_raw:
        nr = _norm_row(r)
        if nr is None:
            return None
        if any(isinstance(v, (dict, list)) or (isinstance(v, (float, Decimal)) and not Decimal(str(v)).is_finite()) for v in r):
            return None
        if rows and len(nr) != len(rows[0]):
            return None
        rows.append(nr)
    cols_raw = raw.get("columns")
    if cols_raw is not None and (not isinstance(cols_raw, list) or any(not isinstance(c, str) or not c.strip() for c in cols_raw)):
        return None
    if cols_raw is not None and rows and len(cols_raw) != len(rows[0]):
        return None
    if raw.get("check_columns") and (not cols_raw or len(set(c.lower() for c in cols_raw)) != len(cols_raw)):
        return None
    columns = (
        tuple(str(c).strip().lower() for c in cols_raw)
        if isinstance(cols_raw, list)
        else None
    )
    return ExpectedResult(
        columns=columns,
        rows=tuple(rows),
        ordered=bool(raw.get("ordered", False)),
        check_columns=bool(raw.get("check_columns", False)),
    )


def parse_expected_state(raw: Any) -> Optional[ExpectedState]:
    """Parse a DML/DDL expected table-state fixture.

    Format: ``{"tables": [{"table": "items", "columns": [...], "rows": [...]}],
    "ordered": false}``. Rows are normalized with the same value rules as
    SELECT results; a missing table is represented by ``{"missing": true}``
    in the actual capture and cannot match a populated expected table.
    """
    if not isinstance(raw, dict) or not isinstance(raw.get("tables"), list):
        return None
    if any(not isinstance(raw.get("ordered", False), bool) for _ in (0,)):
        return None
    tables = []
    names = set()
    for item in raw["tables"]:
        if not isinstance(item, dict):
            return None
        name = item.get("table")
        if not isinstance(name, str) or not name.strip() or name in names:
            return None
        names.add(name)
        missing = item.get("missing", False)
        if type(missing) is not bool:
            return None
        rows_raw = item.get("rows", [])
        if not isinstance(rows_raw, list):
            return None
        rows = []
        for row in rows_raw:
            normalized = _norm_row(row)
            if normalized is None:
                return None
            rows.append(normalized)
        if rows and any(len(row) != len(rows[0]) for row in rows):
            return None
        cols_raw = item.get("columns")
        if cols_raw is not None and (
            not isinstance(cols_raw, list)
            or any(not isinstance(column, str) or not column.strip() for column in cols_raw)
            or (rows and len(cols_raw) != len(rows[0]))
        ):
            return None
        columns = tuple(str(column).strip().lower() for column in cols_raw) if cols_raw else None
        tables.append(ExpectedTable(name.strip(), columns, tuple(rows), missing))
    return ExpectedState(tuple(tables), bool(raw.get("ordered", False)))


def compare_state(actual: list[dict], expected: ExpectedState) -> CompareOutcome:
    """Compare captured table states with a trusted DML fixture."""
    by_name = {str(item.get("table")): item for item in actual if isinstance(item, dict)}
    expected_names = {table.table for table in expected.tables}
    if set(by_name) != expected_names:
        return CompareOutcome("failed", [], ["tables"])
    matched, failed = [], []
    for table in expected.tables:
        captured = by_name[table.table]
        if table.missing:
            (matched if captured.get("missing") else failed).append(f"{table.table}:missing")
            continue
        if captured.get("missing"):
            failed.append(f"{table.table}:missing")
            continue
        columns = [str(column).strip().lower() for column in captured.get("columns", [])]
        if table.columns is not None and columns != list(table.columns):
            failed.append(f"{table.table}:columns")
            continue
        actual_rows = [tuple(_norm_value(value) for value in row)
                       for row in captured.get("rows", [])]
        if expected.ordered:
            rows_equal = actual_rows == list(table.rows)
        else:
            rows_equal = Counter(actual_rows) == Counter(table.rows)
        (matched if rows_equal else failed).append(
            f"{table.table}:rows" if not rows_equal else f"{table.table}:state"
        )
    return CompareOutcome("passed" if not failed else "failed", matched, failed)


def compare(
    columns: list[str],
    rows: list[list],
    expected: ExpectedResult,
    actual_types: Optional[list[str]] = None,
) -> CompareOutcome:
    """Semantic comparison of an executed result against the expected grid."""
    matched: list[str] = []
    failed: list[str] = []

    kinds = actual_types or []
    actual_rows = [tuple(_actual_value(v, kinds[i] if i < len(kinds) else None) for i,v in enumerate(row)) for row in rows]

    width = (
        len(expected.columns)
        if expected.columns is not None
        else (len(expected.rows[0]) if expected.rows else len(columns))
    )

    if expected.check_columns and expected.columns is not None:
        actual_cols = [c.strip().lower() for c in columns]
        if set(actual_cols) == set(expected.columns) and len(
            set(actual_cols)
        ) == len(actual_cols):
            matched.append("columns")
            # Realign rows to the expected column order so positional tuple
            # comparison is fair when the learner ordered columns differently.
            remap = [actual_cols.index(c) for c in expected.columns]
            aligned, misshapen = [], []
            for row in actual_rows:
                if len(row) == len(remap):
                    aligned.append(tuple(row[i] for i in remap))
                else:
                    misshapen.append(row)
            actual_rows = aligned + misshapen
        else:
            failed.append("columns")
    elif len(columns) != width:
        failed.append("column_count")
    else:
        matched.append("columns")
    if expected.ordered:
        rows_equal = actual_rows == list(expected.rows)
    else:
        rows_equal = Counter(actual_rows) == Counter(expected.rows)

    if rows_equal:
        matched.append("rows")
    else:
        failed.append("rows")

    return CompareOutcome(
        status="passed" if not failed else "failed",
        matched=matched,
        failed=failed,
    )
