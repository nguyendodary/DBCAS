"""Original-language authoring; all database writes use disposable fixtures."""
import copy
from types import SimpleNamespace as Record

import pytest

from app.models import Question
from app.repositories import AssessmentRepository
from app.services.evidence_context import capture_question, question_view
from app.services.question_localization import display_content, translation_is_current
from test_admin_questions import _admin, _concept, _mcq_payload, _sql_payload, _essay_payload

BASE = '/api/v1/admin/questions'


def create(client, db, locale='vi', kind='mcq'):
    headers = _admin(client, db)
    concept = _concept(db, 'SOURCE')
    db.commit()
    payload = {'mcq': _mcq_payload, 'sql': _sql_payload, 'essay': _essay_payload}[kind](concept.concept_id)
    payload.update(original_locale=locale)
    payload.pop('translations', None)
    if locale == 'vi':
        payload['prompt'] = 'Chọn mệnh đề lọc các dòng.' if kind == 'mcq' else 'Giải thích hoặc truy vấn bảng students.'
        if kind == 'essay':
            for row in payload['rubrics']:
                row['criteria'] = 'Tiêu chí gốc: ' + row['level_name']
    result = client.post(BASE, headers=headers, json=payload)
    assert result.status_code == 201, result.text
    return headers, payload, result.json()


@pytest.mark.parametrize('locale', ['en', 'vi'])
@pytest.mark.parametrize('kind', ['mcq', 'sql', 'essay'])
def test_original_language_without_translation(client, db_session, locale, kind):
    _, payload, result = create(client, db_session, locale, kind)
    assert result['original_locale'] == locale
    assert result['prompt'] == payload['prompt']
    assert result['translations'] == []
    q = db_session.get(Question, result['question_id'])
    content, shown = display_content(q, 'vi' if locale == 'en' else 'en')
    assert shown == locale and content['prompt'] == payload['prompt']
    if kind == 'sql':
        assert result['reference_answer'] == 'SELECT * FROM students'
        assert result['datasets'][0]['setup_sql'] == payload['datasets'][0]['setup_sql']
    if kind == 'essay':
        assert [(r['level_name'], r['criteria']) for r in result['rubrics']] == [(r['level_name'], r['criteria']) for r in payload['rubrics']]


@pytest.mark.parametrize('locale', ['en', 'vi'])
def test_optional_translation_and_independent_edits(client, db_session, locale):
    headers, payload, result = create(client, db_session, locale)
    qid = result['question_id']
    other = 'vi' if locale == 'en' else 'en'
    translated = {'locale': other, 'prompt': 'Translated question', 'option_texts': {'A': 'WHERE', 'B': 'ORDER BY'}}
    payload['translations'] = [translated]
    result = client.put(f'{BASE}/{qid}', headers=headers, json=payload)
    assert result.status_code == 200, result.text
    assert result.json()['translations'][0]['current']
    assert result.json()['localized_prompts'] == {other: 'Translated question'}
    found = client.get(BASE, headers=headers, params={'q': 'Translated question'}).json()
    assert [row['question_id'] for row in found] == [qid]
    q = db_session.get(Question, qid)
    db_session.refresh(q)
    legacy = Record(question_snapshot=None, question=q)
    legacy_display = question_view(legacy, other)
    assert legacy_display.prompt == q.prompt
    assert legacy_display.content_locale == locale
    assert legacy.question_snapshot is None
    assert question_view(legacy) is q
    snapshot = capture_question(AssessmentRepository(db_session), q)
    before = copy.deepcopy(snapshot)
    assert snapshot['original_locale'] == locale
    assert question_view(Record(question_snapshot=snapshot), other).prompt == 'Translated question'
    assert question_view(Record(question_snapshot=snapshot)).prompt == payload['prompt']

    # Editing only the translation preserves original prose and label-based answer identity.
    payload['translations'][0]['prompt'] = 'Reviewed translated revision'
    result = client.put(f'{BASE}/{qid}', headers=headers, json=payload).json()
    assert result['prompt'] == payload['prompt']
    assert next(o['option_label'] for o in result['options'] if o['is_correct']) == 'A'
    matches = client.get(BASE, headers=headers, params={'q': 'reviewed%REVISION'}).json()
    assert [row['question_id'] for row in matches] == [qid]
    # An old client omitting original_locale may edit a Vietnamese original safely.
    payload.pop('original_locale')
    payload.pop('translations')
    payload['prompt'] += ' Revised original.'
    result = client.put(f'{BASE}/{qid}', headers=headers, json=payload)
    assert result.status_code == 200, result.text
    assert result.json()['original_locale'] == locale
    assert result.json()['translations'][0]['prompt'] == 'Reviewed translated revision'
    assert not result.json()['translations'][0]['current']
    assert result.json()['localized_prompts'] == {}
    assert client.get(BASE, headers=headers, params={'q': 'Reviewed%revision'}).json() == []
    assert other in result.json()['missing_locales']
    assert snapshot == before
    assert question_view(Record(question_snapshot=snapshot), other).prompt == 'Translated question'


def test_original_language_cannot_be_relabelled(client, db_session):
    headers, payload, result = create(client, db_session)
    payload['original_locale'] = 'en'
    response = client.put(f"{BASE}/{result['question_id']}", headers=headers, json=payload)
    assert response.status_code == 422
    assert client.get(f"{BASE}/{result['question_id']}", headers=headers).json()['original_locale'] == 'vi'


def test_learner_cannot_approve_or_create_question_translations(client, db_session):
    from test_rbac import _register
    headers, payload, question = create(client, db_session)
    qid = question['question_id']
    before = client.get(f'{BASE}/{qid}', headers=headers).json()
    payload['translations'] = [{'locale': 'en', 'prompt': 'Unauthorized translation',
                                'option_texts': {'A': 'WHERE', 'B': 'ORDER BY'}}]
    learner = {'Authorization': 'Bearer ' + _register(client, 'translation-learner@test.dev')}
    for auth, expected in (({}, 401), (learner, 403)):
        assert client.post(BASE, headers=auth, json=payload).status_code == expected
        assert client.put(f'{BASE}/{qid}', headers=auth, json=payload).status_code == expected
    assert client.get(f'{BASE}/{qid}', headers=headers).json() == before


@pytest.mark.parametrize('duplicate', [False, True])
def test_translation_cannot_use_original_or_duplicate_locale(client, db_session, duplicate):
    headers, payload, result = create(client, db_session)
    item = {'locale': 'en' if duplicate else 'vi', 'prompt': 'Text', 'option_texts': {'A': 'WHERE', 'B': 'ORDER BY'}}
    payload['translations'] = [item, item] if duplicate else [item]
    response = client.put(f"{BASE}/{result['question_id']}", headers=headers, json=payload)
    assert response.status_code == 422


def test_old_snapshot_defaults_to_english_without_mutation():
    old = {'question_id': 1, 'question_type': 'mcq', 'prompt': 'Old English prompt', 'points': '1', 'options': [], 'rubrics': []}
    before = copy.deepcopy(old)
    assert question_view(Record(question_snapshot=old), 'vi').content_locale == 'en'
    assert old == before


def test_concept_and_difficulty_validation_remains_required(client, db_session):
    headers, payload, result = create(client, db_session)
    qid = result['question_id']
    payload['difficulty_level'] = 6
    assert client.put(f'{BASE}/{qid}', headers=headers, json=payload).status_code == 422
    payload['difficulty_level'] = 1
    payload['concept_ids'] = []
    assert client.put(f'{BASE}/{qid}', headers=headers, json=payload).status_code == 200
    assert client.patch(f'{BASE}/{qid}', headers=headers, json={'status': 'validated'}).status_code == 422


def test_existing_english_hash_and_translation_remain_current(client, db_session):
    from app.services.question_localization import source_fingerprint
    headers = _admin(client, db_session)
    concept = _concept(db_session, 'LEGACY')
    db_session.commit()
    payload = _mcq_payload(concept.concept_id)
    result = client.post(BASE, headers=headers, json=payload).json()
    q = db_session.get(Question, result['question_id'])
    historical_source = Record(question_type=q.question_type, prompt=q.prompt, explanation=q.explanation, options=q.options, rubrics=q.rubrics)
    assert source_fingerprint(historical_source) == source_fingerprint(q)
    assert translation_is_current(q, q.translations[0])
    assert display_content(q, 'vi')[1] == 'vi'


@pytest.mark.parametrize('kind', ['mcq', 'sql', 'essay'])
@pytest.mark.parametrize('translated', [False, True])
def test_vietnamese_original_session_locale_and_evidence(client, db_session, kind, translated):
    from test_draft_lifecycle import _fixture, _save
    from app.services.question_localization import upsert_question_translations
    _, session, attempt, q, _, headers, answer = _fixture(db_session, kind, 'en')
    q.original_locale = 'vi'
    q.prompt = 'Nội dung gốc: SELECT id FROM t.'
    if kind == 'essay':
        for band in q.rubrics:
            band.criteria = 'Tiêu chí gốc ' + band.level_name
    if translated:
        upsert_question_translations(db_session, q, [{'locale': 'en', 'prompt': 'Reviewed English SELECT id FROM t.',
            'option_texts': {o.option_label: o.option_text for o in q.options},
            'rubrics': {r.level_name: {'label': r.level_name, 'criteria': 'Reviewed English criteria'} for r in q.rubrics}}])
    attempt.question_snapshot = capture_question(AssessmentRepository(db_session), q)
    db_session.commit()
    original = copy.deepcopy(attempt.question_snapshot)
    expected = 'Reviewed English SELECT id FROM t.' if translated else q.prompt
    assert _save(client, session, q, headers, answer).status_code == 200
    for requested in ('vi', 'en'):
        state = client.get(f'/api/v1/sessions/{session.session_id}', headers={**headers, 'Accept-Language': requested}).json()
        assert state['current_question']['content_locale'] == ('en' if translated else 'vi')
        assert state['current_question']['prompt'] == expected
        assert state['current_question']['draft'] == answer
    for display_locale in ('vi', 'en'):
        assert client.get(f'/api/v1/sessions/{session.session_id}',
            params={'display_locale': display_locale}).status_code == 401
        displayed = client.get(f'/api/v1/sessions/{session.session_id}', headers=headers,
            params={'display_locale': display_locale})
        assert displayed.status_code == 200
        item = displayed.json()['current_question']
        assert displayed.json()['locale'] == 'en'  # recorded locale is immutable
        assert item['prompt'] == (expected if display_locale == 'en' else q.prompt)
        assert item['draft'] == answer
        assert [o['option_id'] for o in item['options']] == [o.option_id for o in q.options]
        assert all('is_correct' not in o for o in item['options'])
    assert client.get(f'/api/v1/sessions/{session.session_id}', headers=headers,
        params={'display_locale': 'fr'}).status_code == 422
    # Empty finalization exercises evidence without executing SQL or invoking a provider.
    assert _save(client, session, q, headers, {}, revision=2).status_code == 200
    assert client.post(f'/api/v1/sessions/{session.session_id}/finish', headers=headers).status_code == 200
    evidence = client.get(f'/api/v1/sessions/{session.session_id}/evidence', headers=headers).json()['items'][0]
    assert evidence['prompt'] == expected
    assert evidence['content_locale'] == ('en' if translated else 'vi')
    displayed_evidence = client.get(f'/api/v1/sessions/{session.session_id}/evidence',
        headers=headers, params={'display_locale': 'vi'}).json()['items'][0]
    assert displayed_evidence['prompt'] == q.prompt
    assert displayed_evidence['score'] == evidence['score']
    assert displayed_evidence['grading_detail'] == evidence['grading_detail']
    assert question_view(attempt).prompt == q.prompt  # grading always reads the original
    if kind == 'essay':
        assert all(r.criteria.startswith('Tiêu chí gốc') for r in question_view(attempt).rubrics)
    db_session.refresh(attempt)
    assert attempt.question_snapshot == original


def test_used_vietnamese_question_forks_without_rewriting_evidence(db_session):
    from test_draft_lifecycle import _fixture
    from app.schemas import QuestionUpsertRequest
    from app.services import question_service as service
    from app.services.question_localization import upsert_question_translations
    _, _, attempt, q, concept, _, _ = _fixture(db_session)
    q.original_locale = 'vi'
    q.prompt = 'Nội dung gốc'
    upsert_question_translations(db_session, q, [{'locale': 'en', 'prompt': 'Reviewed original', 'option_texts': {o.option_label: o.option_text for o in q.options}}])
    attempt.question_snapshot = capture_question(AssessmentRepository(db_session), q)
    db_session.commit()
    old_snapshot = copy.deepcopy(attempt.question_snapshot)
    old_ids = [o.option_id for o in q.options]
    detail = service.get_question(db_session, q.question_id)
    payload = detail.model_dump(exclude={'translations'})
    payload.update(prompt='Nội dung mới', concept_ids=[concept.concept_id])
    revised = service.replace_question(db_session, q.question_id, QuestionUpsertRequest(**payload))
    assert revised.question_id != q.question_id
    assert revised.original_locale == 'vi'
    assert revised.translations[0].prompt == 'Reviewed original'
    assert not revised.translations[0].current
    db_session.refresh(attempt)
    assert attempt.question_snapshot == old_snapshot
    assert attempt.question_id == q.question_id
    assert [o.option_id for o in q.options] == old_ids


def test_vietnamese_essay_grading_uses_original_criteria_with_mock_provider(db_session):
    from test_draft_lifecycle import _fixture
    from test_essay_grading import StubLLM
    from app.services.essay_grading import grade_essay
    _, _, attempt, q, _, _, _ = _fixture(db_session, 'essay')
    q.original_locale = 'vi'
    q.prompt = 'Giải thích chuẩn hóa.'
    for band in q.rubrics:
        band.criteria = 'Tiêu chí gốc ' + band.level_name
    attempt.question_snapshot = capture_question(AssessmentRepository(db_session), q)
    answer = 'Giải thích chuẩn hóa đầy đủ.'
    provider = StubLLM(response={'rubric_level': 'Complete', 'score': 1, 'matched_criteria': ['Tiêu chí gốc Complete'],
        'missing_concepts': [], 'evidence': [answer], 'explanation': 'Đáp ứng tiêu chí.', 'feedback': 'Luyện tập thêm.'})
    original = question_view(attempt)
    result = grade_essay(original, original.rubrics, answer, provider, locale='vi')
    prompt = provider.calls[0]['messages'][-1].content
    assert 'Giải thích chuẩn hóa.' in prompt
    assert 'Tiêu chí gốc Complete' in prompt
    assert result['score'] == 1
    assert result['grading_detail']['rubric_level'] == 'Complete'
