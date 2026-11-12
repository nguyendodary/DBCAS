"""Regression for empty grading evidence and typed multiset semantics."""
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.errors import AppError
from app.services.sql_grading import grade_sql
from app.services.sql_result import compare, parse_expected


def test_no_datasets_never_awards_full_marks():
    with pytest.raises(AppError) as exc:
        grade_sql(SimpleNamespace(points=Decimal("10")), [], [], "SELECT 1", None)
    assert exc.value.code == "dataset_not_configured"
    assert exc.value.status_code == 422


@pytest.mark.parametrize("rows,expected,types,passed", [
    ([["1.000"]], [[1]], ["number"], True),
    ([["1.000"]], [[1]], ["text"], False),
    ([[True]], [[1]], ["boolean"], False),
    ([[None], [1], [1]], [[1], [None], [1]], ["number"], True),
    ([[1]], [[1], [1]], ["number"], False),
])
def test_typed_multiset_comparison(rows, expected, types, passed):
    reference = parse_expected({"columns": ["x"], "rows": expected})
    assert (compare(["alias"], rows, reference, types).status == "passed") is passed
