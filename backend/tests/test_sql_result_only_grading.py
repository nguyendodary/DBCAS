"""Result-only grading policy; no application database or Docker required."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services.sandbox_runner import SandboxResult
from app.services.sql_grading import grade_sql


@pytest.mark.parametrize('rows,columns,score', [
    ([['Binh'], ['An']], ['different_alias'], '10'),
    ([['An'], ['Binh']], ['name'], '10'),
    ([['An']], ['name'], '0'),
    ([['An'], ['Binh'], ['An']], ['name'], '0'),
    ([['An'], ['Other']], ['name'], '0'),
    ([['An', 1], ['Binh', 2]], ['name', 'extra'], '0'),
])
def test_only_result_values_and_shape_determine_match(rows, columns, score):
    expected = {'columns': ['name'], 'rows': [['An'], ['Binh']], 'ordered': True, 'check_columns': True}
    dataset = SimpleNamespace(dataset_name='data', setup_sql='CREATE TABLE students (name TEXT)',
                              is_edge_case=False, expected_result=expected)
    runner = Mock()
    runner.provision_dataset.return_value = 'ds_test'
    runner.execute.return_value = SandboxResult(success=True, columns=columns, rows=rows, row_count=len(rows))
    question = SimpleNamespace(points=Decimal('10'))
    result = grade_sql(question, [dataset], ['Joins'], 'SELECT name AS different_alias FROM students ORDER BY name DESC', runner)
    assert result['score'] == Decimal(score)
    assert result['grading_detail']['missing_required_concepts'] == []
    assert expected['ordered'] is True and expected['check_columns'] is True
    runner.drop_dataset.assert_called_once_with('ds_test')
