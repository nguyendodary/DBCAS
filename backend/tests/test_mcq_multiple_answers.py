from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace as Row

import pytest

from app.errors import AppError
from app.schemas import SubmitAnswerRequest, QuestionUpsertRequest
from app.services.assessment_lifecycle import _answer_dict, _persist_answer, grade_attempt
from app.services.grading_service import score_mcq
from app.services.question_service import _check_type_payload


def question():
    return Row(question_type='mcq', points=Decimal('2'), options=[
        Row(option_id=1, is_correct=True), Row(option_id=2, is_correct=True),
        Row(option_id=3, is_correct=False), Row(option_id=4, is_correct=False)])


@pytest.mark.parametrize('selected,expected', [([1, 2], 2), ([2, 1], 2), ([1], 0),
    ([2], 0), ([1, 2, 3], 0), ([3, 4], 0), ([], 0)])
def test_exact_answer_set(selected, expected):
    q = question()
    result = score_mcq(q, q.options, selected_option_ids=selected)
    assert result['score'] == Decimal(expected)
    assert result['grading_detail']['selected_option_ids'] == sorted(selected)
    assert result['grading_detail']['correct_option_ids'] == [1, 2]


@pytest.mark.parametrize('ids', [[1, 1], [99]])
def test_reject_duplicates_and_foreign_options(ids):
    q = question()
    with pytest.raises(AppError) as error:
        _answer_dict(SubmitAnswerRequest(question_id=10, selected_option_ids=ids), q)
    assert error.value.code == 'invalid_option'


def test_legacy_single_answer_remains_supported():
    q = question()
    q.options[1].is_correct = False
    assert score_mcq(q, q.options, 1)['score'] == Decimal(2)
    assert score_mcq(q, q.options, None)['score'] == Decimal(0)


def test_array_normalization_and_submission_storage():
    payload = SubmitAnswerRequest(question_id=10, selected_option_ids=[2, 1])
    answer = _answer_dict(payload, question())
    assert answer == {'selected_option_ids': [1, 2]}
    attempt = Row()
    _persist_answer(attempt, answer, datetime.now(timezone.utc))
    assert attempt.selected_option_ids == [1, 2]
    assert attempt.selected_option_id is None
    assert attempt.submission_hash


def test_cannot_mix_answer_formats():
    for payload in [SubmitAnswerRequest(question_id=10, selected_option_id=1, selected_option_ids=[1]),
                    SubmitAnswerRequest(question_id=10, selected_option_ids=[1], sql_answer='SELECT 1')]:
        with pytest.raises(AppError):
            _answer_dict(payload, question())
    with pytest.raises(AppError):
        _answer_dict(SubmitAnswerRequest(question_id=10, selected_option_ids=[]), Row(question_type='essay'))


def test_bank_accepts_multiple_keys_but_rejects_missing_key():
    payload = QuestionUpsertRequest(question_type='mcq', prompt='Pick all correct answers', points=1,
        options=[{'option_label': 'A', 'option_text': 'First', 'is_correct': True},
                 {'option_label': 'B', 'option_text': 'Second', 'is_correct': True}])
    _check_type_payload(payload)
    for option in payload.options:
        option.is_correct = False
    with pytest.raises(AppError):
        _check_type_payload(payload)


def test_grading_uses_frozen_answer_key():
    snapshot = dict(question_id=10, question_type='mcq', prompt='Choose', points='2',
        difficulty_level=1, options=[dict(option_id=1, option_label='A', option_text='First', is_correct=True),
                                   dict(option_id=2, option_label='B', option_text='Second', is_correct=True)])
    attempt = Row(question_snapshot=snapshot)
    result = grade_attempt(None, attempt, None, {'selected_option_ids': [2, 1]}, None, None)
    assert result['score'] == Decimal(2)
