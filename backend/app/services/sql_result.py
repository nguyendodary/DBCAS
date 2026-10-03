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


def _norm_value(v: Any) -> Any:
    """Map a JSON value into a comparison-stable primitive.

    All numbers become Decimal (value equality, scale-insensitive); bools and
    None keep their identity; everything else compares as stripped strings so
    e.g. dates delivered as "2024-01-05" match textually.
    """
    if v is None or isinstance(v, bool):
        return v
    if isinstance(v, (int, float, Decimal)):
        try:
            return Decimal(str(v))
        except InvalidOperation:
            return str(v).strip()
    if isinstance(v, str):
        return v.strip()
    return str(v)


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
    rows = []
    for r in rows_raw:
        nr = _norm_row(r)
        if nr is None:
            return None
        rows.append(nr)
    cols_raw = raw.get("columns")
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


def compare(
    columns: list[str],
    rows: list[list],
    expected: ExpectedResult,
) -> CompareOutcome:
    """Semantic comparison of an executed result against the expected grid."""
    matched: list[str] = []
    failed: list[str] = []

    actual_rows = [tuple(_norm_value(v) for v in row) for row in rows]

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
