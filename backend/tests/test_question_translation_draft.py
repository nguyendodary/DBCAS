"""Draft-only translation through the real structured provider and MockTransport."""
import copy
import json

import httpx
import pytest

from app.config import Settings, get_settings
from app.deps import get_translation_llm
from app.errors import AppError
from app.main import app
from app.schemas import QuestionUpsertRequest
from app.services.llm import LLMService, ChatCompletionsProvider, LLMError
from app.services.question_translation import prepare, DraftBudget, capability


def settings(**changes):
    return Settings(_env_file=None, question_translation_enabled=True, llm_base_url="https://translation.test/v1",
                    llm_api_key="mock-only", llm_model="mock-translator", llm_max_retries=0,
                    jwt_secret="test-secret-not-for-production-123456", **changes)


def payload(kind="mcq", locale="vi"):
    values = dict(question_type=kind, original_locale=locale, points=1,
                  prompt="Giải thích `SELECT id FROM students` và $x + y = 2$.",
                  explanation="Giữ nguyên SQL và công thức.")
    if kind == "mcq":
        values['options'] = [dict(option_label="A", option_text="WHERE", is_correct=True),
                             dict(option_label="B", option_text="ORDER BY", is_correct=False)]
    if kind == "sql":
        values.update(reference_answer="SELECT id FROM students",
                      datasets=[dict(dataset_name="base", setup_sql="CREATE TABLE students(id int)", expected_result={"rows": []})])
        values['prompt'] += " Truy vấn students.id bằng SELECT id FROM students."
    if kind == "essay":
        values['rubrics'] = [dict(level_name="Complete", min_score=1, max_score=1, criteria="Đủ 2 điều kiện và $a = b$.")]
    return QuestionUpsertRequest(**values)


def service(transform=None, status=200):
    calls = []
    def respond(request):
        body=json.loads(request.content);calls.append(body)
        fields=json.loads(body['messages'][-1]['content'])['fields']
        result={k: (v if v.startswith('__DBCAS_T') and v.endswith('__') and v.count('__DBCAS_T')==1 else 'Translated: '+v) for k,v in fields.items()}
        if transform:
            result=transform(result)
        return httpx.Response(status,json={"choices":[{"message":{"content":json.dumps(result)}}]})
    config=settings()
    provider=ChatCompletionsProvider(config.llm_base_url, config.llm_api_key, transport=httpx.MockTransport(respond), max_retries=0)
    return LLMService(config,provider=provider), calls


@pytest.mark.parametrize("locale", ["vi", "en"])
@pytest.mark.parametrize("kind", ["mcq", "sql", "essay"])
def test_draft_preserves_technical_content_and_never_changes_source(kind, locale):
    source=payload(kind,locale);before=copy.deepcopy(source.model_dump())
    llm,calls=service()
    result=prepare(source,1,settings(),llm,limiter=DraftBudget())
    assert result['status']=='draft'
    assert result['translation']['locale']==('en' if locale=='vi' else 'vi')
    assert '`SELECT id FROM students`' in result['translation']['prompt']
    assert '$x + y = 2$' in result['translation']['prompt']
    assert source.model_dump()==before
    assert 'is_correct' not in calls[0]['messages'][-1]['content']
    assert 'CREATE TABLE' not in calls[0]['messages'][-1]['content']
    if kind=='mcq':assert result['translation']['option_texts']=={'A':'WHERE','B':'ORDER BY'}
    if kind=='sql':assert 'students.id' in result['translation']['prompt']
    if kind=='essay':
        assert list(result['translation']['rubrics'])==['Complete']
        assert '$a = b$' in result['translation']['rubrics']['Complete']['criteria']
        assert source.rubrics[0].max_score==1


def test_changed_or_missing_technical_tokens_are_rejected():
    llm,_=service(lambda r:{**r,'prompt':r['prompt'].replace('__DBCAS_T0000__','invented')})
    with pytest.raises(LLMError,match='protected technical'):
        prepare(payload(),1,settings(),llm,limiter=DraftBudget())


def test_exact_technical_answer_cannot_gain_extra_prose():
    llm,_=service(lambda r:{**r,'option_A':'extra '+r['option_A']})
    with pytest.raises(LLMError,match='Technical-only'):
        prepare(payload(),1,settings(),llm,limiter=DraftBudget())


def test_english_select_instruction_is_not_mistaken_for_executable_sql():
    source=payload(locale='en').model_copy(update={'prompt':'Select the correct database clause.'})
    llm,calls=service()
    prepare(source,1,settings(),llm,limiter=DraftBudget())
    fields=json.loads(calls[0]['messages'][-1]['content'])['fields']
    assert fields['prompt']=='Select the correct database clause.'


@pytest.mark.parametrize('status',[429,503])
def test_provider_failure_is_reported_once_without_mutation(status):
    source=payload();before=source.model_dump();llm,calls=service(status=status)
    with pytest.raises(LLMError):prepare(source,1,settings(),llm,limiter=DraftBudget())
    assert len(calls)==1 and source.model_dump()==before


def test_disabled_feature_does_not_use_grading_credentials():
    llm,calls=service();s=settings().model_copy(update={'question_translation_enabled':False})
    assert capability(s)=={'available':False}
    with pytest.raises(AppError):prepare(payload(),1,s,llm)
    assert not calls


def test_quota_is_bounded_per_admin_and_process():
    clock=[0];b=DraftBudget(lambda:clock[0])
    b.take(1);b.take(1)
    with pytest.raises(AppError):b.take(1)
    clock[0]=61
    for i in range(2,20):b.take(i)
    with pytest.raises(AppError):b.take(21)
    clock[0]=3700;b.take(1)


def test_admin_route_returns_unpersisted_draft_and_rejects_learner(client,db_session,monkeypatch):
    from test_admin_questions import _admin
    from test_rbac import _register
    from app.models import Question,QuestionTranslation
    import app.services.question_translation as module
    admin=_admin(client,db_session);learner={'Authorization':'Bearer '+_register(client,'draft-learner@test.dev')}
    llm,calls=service();monkeypatch.setattr(module,'budget',DraftBudget())
    original_counts=(db_session.query(Question).count(),db_session.query(QuestionTranslation).count())
    app.dependency_overrides[get_settings]=lambda:settings()
    app.dependency_overrides[get_translation_llm]=lambda:llm
    try:
        endpoint='/api/v1/admin/question-translation/draft';body=payload().model_dump(mode='json')
        assert client.post(endpoint,json=body).status_code==401
        assert client.post(endpoint,headers=learner,json=body).status_code==403
        assert client.get('/api/v1/admin/question-translation/capability',headers=learner).status_code==403
        response=client.post(endpoint,headers=admin,json=body)
        assert response.status_code==200,response.text
        assert response.json()['status']=='draft'
        assert len(calls)==1
        assert (db_session.query(Question).count(),db_session.query(QuestionTranslation).count())==original_counts
    finally:
        app.dependency_overrides.pop(get_settings,None);app.dependency_overrides.pop(get_translation_llm,None)
