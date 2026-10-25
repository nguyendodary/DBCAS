from types import SimpleNamespace as Row
from app.services.bank_validation import sql_fixture_problems


def dataset(edge=False):
    return Row(dataset_name='dataset_1', setup_sql='CREATE TABLE sample (id INTEGER); INSERT INTO sample VALUES (1);',
               expected_result={'columns': ['id'], 'rows': [[1]]}, is_edge_case=edge)


def test_one_regular_dataset_is_enough():
    assert sql_fixture_problems([dataset()], 'SELECT id FROM sample') == []


def test_edge_flag_is_not_required_and_legacy_flag_is_accepted():
    assert sql_fixture_problems([dataset(True)], 'SELECT id FROM sample') == []


def test_missing_data_or_answer_is_still_rejected():
    assert sql_fixture_problems([], 'SELECT id FROM sample')
    assert sql_fixture_problems([dataset()], '')
