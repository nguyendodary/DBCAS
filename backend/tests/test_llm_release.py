"""Real application LLM service and mocked provider transport release gates."""
import json
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select

from app.config import Settings
from app.models import Concept, CourseLearningOutcome, Question, LlmCache
from app.repositories import LlmCacheRepository
from app.services.ai_admin_service import suggest_clo_concepts, suggest_question_tags, generate_candidates
from app.services.essay_grading import grade_essay
from app.services.llm import ChatMessage, LLMService, LLMError, ChatCompletionsProvider
from app.services.llm.sanitize import sanitize_learner_text
from app.services.rubric_validation import rubric_problems
from app.schemas import CandidateGenerateRequest


RUBRICS = [
    {"level_name": "Incomplete", "min_score": 0, "max_score": .24, "criteria": "No correct explanation"},
    {"level_name": "Partial", "min_score": .25, "max_score": .49, "criteria": "Definition only"},
    {"level_name": "Mostly Complete", "min_score": .50, "max_score": .74, "criteria": "Definition and example; minor omission"},
    {"level_name": "Complete", "min_score": .75, "max_score": 1, "criteria": "Definition, example, conditions"},
]


def _service(db, response, *, seen=None, **settings):
    def handler(request):
        if seen is not None:
            seen.append(json.loads(request.content))
        raw = response if isinstance(response, str) else json.dumps(response)
        return httpx.Response(200, json={"choices": [{"message": {"content": raw}}]})
    config = Settings(_env_file=None, llm_api_key="test-key", llm_base_url="https://provider.test/v1", llm_model="test-model", **settings)
    return LLMService(config, provider=ChatCompletionsProvider("https://provider.test/v1", "test-key", transport=httpx.MockTransport(handler)), cache=LlmCacheRepository(db))


def _grade_payload(**over):
    result = {"rubric_level": "Complete", "score": .9, "explanation": "Definition and conditions are accurate.", "feedback": "Continue with decomposition exercises.", "matched_criteria": ["definition"], "missing_concepts": [], "evidence": ["3NF"]}
    result.update(over)
    return result


def _rubrics():
    from types import SimpleNamespace
    return [SimpleNamespace(**{**r, "min_score": Decimal(str(r["min_score"])), "max_score": Decimal(str(r["max_score"]))}) for r in RUBRICS]


def _essay():
    return Question(question_type="essay", prompt="Explain 3NF", points=Decimal("1"), reference_answer="Definition and example")


@pytest.mark.parametrize("over", [
    {"score": float("nan")}, {"score": float("inf")}, {"score": float("-inf")},
    {"score": True}, {"score": "0.9"}, {"score": 2}, {"score": -.1},
    {"explanation": None}, {"explanation": ""}, {"feedback": " "},
    {"rubric_level": "Excellent"}, {"rubric_level": "Partial", "score": .9},
    {"matched_criteria": "definition"}, {"evidence": [42]}, {"evidence": ["invented quote"]},
    {"confidence": 2}, {"confidence": float("nan")},
])
def test_invalid_essay_never_cached(db_session, over):
    with pytest.raises(LLMError):
        grade_essay(_essay(), _rubrics(), "3NF explanation", _service(db_session, _grade_payload(**over)))
    assert list(db_session.scalars(select(LlmCache))) == []


@pytest.mark.parametrize("missing", ["score", "rubric_level", "explanation", "feedback", "matched_criteria", "missing_concepts", "evidence"])
def test_missing_grade_field_rejected(db_session, missing):
    result = _grade_payload()
    result.pop(missing)
    with pytest.raises(LLMError):
        grade_essay(_essay(), _rubrics(), "3NF", _service(db_session, result))
    assert not db_session.scalar(select(LlmCache))


def test_valid_essay_is_cached_only_after_domain_validation(db_session):
    seen = []
    service = _service(db_session, _grade_payload(), seen=seen)
    first = grade_essay(_essay(), _rubrics(), "3NF", service)
    second = grade_essay(_essay(), _rubrics(), "3NF", service)
    assert first == second and first["score"] == Decimal(".9")
    assert len(seen) == 1
    assert seen[0]["temperature"] == .1
    assert "Calibration examples" in seen[0]["messages"][0]["content"]
    assert db_session.scalar(select(LlmCache)).task_type == "essay_score"


@pytest.mark.parametrize("rows", [RUBRICS[:1], RUBRICS[:3], RUBRICS+[RUBRICS[0]], [{**r, "level_name": "Wrong"} for r in RUBRICS], [{**r, "max_score": .5} if i==0 else r for i,r in enumerate(RUBRICS)], [{**r, "min_score": .26} if i==1 else r for i,r in enumerate(RUBRICS)], [{**r, "max_score": 2} if i==3 else r for i,r in enumerate(RUBRICS)]])
def test_invalid_rubrics_rejected(rows):
    assert rubric_problems(rows, 1)


def test_valid_canonical_rubric():
    assert rubric_problems(RUBRICS, 1) == []


@pytest.mark.parametrize("text", ["transaction", "analysis", "mandatory", "SELECT annual_total FROM transactions", "SELECT 2026, 100000, 1234, '3NF';"])
def test_short_name_does_not_corrupt_technical_content(text):
    assert sanitize_learner_text(text, identifiers=["An"]) == text


def test_known_identifier_boundaries_and_contextual_numbers():
    out = sanitize_learner_text("An wrote transaction analysis. student id 20210045. SELECT 20210045; mail an@school.edu", identifiers=["An", "an@school.edu"])
    assert "transaction analysis" in out and "SELECT 20210045" in out
    assert out.startswith("[name] wrote") and "student id [id]" in out and "an@school.edu" not in out


def test_redaction_is_idempotent_even_when_name_matches_placeholder():
    once = sanitize_learner_text("Name explained transactions, id 20210045", identifiers=["Name"])
    assert sanitize_learner_text(once, identifiers=["Name"]) == once


@pytest.mark.parametrize("text", ["SELECT * FROM t WHERE id = 1234;", "SELECT 123-456-7890;",
    "A record 1234 has a foreign key.", "SELECT id, record FROM t WHERE record = 20210045;",
    "SELECT 090-123-4567 AS arithmetic;"])
def test_redaction_preserves_ordinary_sql_identifiers_and_arithmetic(text):
    assert sanitize_learner_text(text, identifiers=["An"]) == text


def test_known_profile_phone_and_id_are_redacted_without_generic_sql_matching():
    text = "Call 090-123-4567. account id 17. SELECT id = 1234;"
    out = sanitize_learner_text(text, identifiers=["090-123-4567", "account id 17"])
    assert "090-123-4567" not in out and "account id 17" not in out
    assert "SELECT id = 1234" in out


def test_all_outbound_messages_are_redacted(db_session):
    seen=[]
    service=_service(db_session,{"ok":True},seen=seen)
    service.generate_structured("tag",[ChatMessage("system","admin@school.edu"),ChatMessage("user","An, student id 20210045, transaction analysis")],identifiers=["An"])
    wire=json.dumps(seen)
    assert "admin@school.edu" not in wire and "20210045" not in wire
    assert "transaction analysis" in wire


def _curriculum(db):
    from app.models import Account
    admin=Account(email="curation@test.dev",password_hash="unused",status="active")
    db.add(admin);db.flush()
    concept=Concept(concept_code="SQL-SELECT",concept_name="SELECT",subject_area="SQL Querying",difficulty_level=1)
    db.add(concept);db.flush()
    clo=CourseLearningOutcome(clo_code="CLO-QUERY",title="Write safe queries",created_by=admin.account_id)
    question=Question(question_type="mcq",prompt="What selects rows?",points=Decimal("1"),difficulty_level=1,created_by=admin.account_id,status="draft")
    db.add_all([clo,question]);db.commit()
    return admin,concept,clo,question


def test_clo_mapping_through_real_service_and_mock_http(db_session):
    _,concept,clo,_=_curriculum(db_session)
    seen=[]
    result=suggest_clo_concepts(db_session,clo.clo_id,_service(db_session,{"concept_ids":[concept.concept_id],"rationale":"Matches the query outcome"},seen=seen))
    assert result.clo.concepts[0].status == "pending"
    assert seen[0]["messages"][0]["role"] == "system"
    assert db_session.scalar(select(LlmCache)).task_type == "clo_map"


def test_question_tagging_through_real_service_and_mock_http(db_session):
    _,concept,_,q=_curriculum(db_session)
    result=suggest_question_tags(db_session,q.question_id,_service(db_session,{"concept_ids":[concept.concept_id],"difficulty_level":2,"evaluation_criteria":"Recognize SELECT"}))
    assert result.question.concepts[0].confirmed is False
    assert result.suggested_difficulty == 2
    assert q.difficulty_level == 1


def test_candidates_through_real_service_and_mock_http(db_session):
    admin,concept,_,_=_curriculum(db_session)
    payload={"questions":[{"prompt":"Choose the SQL projection clause","difficulty_level":1,"options":[{"option_label":"A","option_text":"SELECT","is_correct":True},{"option_label":"B","option_text":"DELETE","is_correct":False}]}]}
    result=generate_candidates(db_session,CandidateGenerateRequest(concept_id=concept.concept_id,question_type="mcq",count=1),admin,_service(db_session,payload),None)
    assert len(result)==1 and result[0].promoted_question_id is None
    assert db_session.scalar(select(LlmCache)).task_type == "gen_question"


@pytest.mark.parametrize("task,payload", [("clo_map",{"concept_ids":[True],"rationale":"x"}),("tag",{"concept_ids":[1],"difficulty_level":99,"evaluation_criteria":"x"}),("gen_question",{"questions":[{"prompt":"x","difficulty_level":1}]})])
def test_domain_invalid_admin_output_not_cached(db_session,task,payload):
    admin,concept,clo,q=_curriculum(db_session)
    service=_service(db_session,payload)
    with pytest.raises(LLMError):
        if task=="clo_map":suggest_clo_concepts(db_session,clo.clo_id,service)
        elif task=="tag":suggest_question_tags(db_session,q.question_id,service)
        else:generate_candidates(db_session,CandidateGenerateRequest(concept_id=concept.concept_id,question_type="mcq",count=1),admin,service,None)
    assert not db_session.scalar(select(LlmCache))


def test_failed_cache_insert_keeps_primary_transaction_usable(db_session):
    from app.models import Account
    cache=LlmCacheRepository(db_session)
    cache.store("a"*64,"tag","test",{"ok":True})
    with pytest.raises(Exception):cache.store("a"*64,"tag","test",{"ok":True})
    db_session.add(Account(email="survives@test.dev",password_hash="unused",status="active"))
    db_session.commit()
    assert db_session.scalar(select(Account).where(Account.email=="survives@test.dev"))


def test_prompt_context_provider_and_token_budget_version_cache(db_session):
    seen=[]
    first=_service(db_session,{"ok":True},seen=seen)
    messages=[ChatMessage("user","same")]
    first.generate_structured("tag",messages,max_tokens=100,context_version="v1")
    first.generate_structured("tag",messages,max_tokens=200,context_version="v1")
    first.generate_structured("tag",messages,max_tokens=200,context_version="v2")
    _service(db_session,{"ok":True},seen=seen,llm_prompt_version="next").generate_structured("tag",messages,max_tokens=200,context_version="v2")
    assert len(seen)==4
