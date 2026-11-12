"""Strict mocked-provider authoring through real services and database."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from uuid import uuid4

import pytest
from sqlalchemy import select, text

from app.db import get_session_factory
from app.errors import AppError
from app.models import Concept, LlmCache, Question, QuestionCandidate
from app.schemas import CandidateGenerateRequest, CandidateApprovalRequest
from app.services.ai_admin_service import generate_candidates, approve_candidate, validate_candidate, reject_candidate
from app.services.llm import LLMError
from app.services.sandbox_runner import SandboxRunner
from app.config import get_settings
from generation_fixtures import grounded, DESCRIPTION, KEYWORDS, OBJECTIVES
from test_adaptive_engine import _make_account
from test_llm_release import _service, RUBRICS


def fixture(db, kind="mcq", locale="en", difficulty="EASY"):
    admin = _make_account(db, "governed-admin@test.dev", "Administrator")
    concept = Concept(concept_code="SQL-SELECT", concept_name="SELECT", subject_area="SQL Querying",
                      description=DESCRIPTION, keywords=KEYWORDS, learning_objectives=OBJECTIVES)
    db.add(concept)
    db.commit()
    item = {"prompt": "Select all identifiers in the supplied table.", "difficulty_level": 1}
    if kind == "mcq":
        item.update(prompt="Which SQL clause chooses result columns?", options=[
            {"option_label": "A", "option_text": "SELECT", "is_correct": True},
            {"option_label": "B", "option_text": "DROP", "is_correct": False}])
    elif kind == "sql":
        item.update(reference_answer="SELECT id FROM t", datasets=[
            {"dataset_name": "base", "setup_sql": "CREATE TABLE t(id int); INSERT INTO t VALUES (1);",
             "expected_result": {"columns": ["id"], "rows": [[1]]}, "is_edge_case": False},
            {"dataset_name": "empty", "setup_sql": "CREATE TABLE t(id int);",
             "expected_result": {"columns": ["id"], "rows": []}, "is_edge_case": True}])
    else:
        item.update(prompt="Explain projection and filtering.", reference_answer="SELECT projects columns; WHERE filters rows.", rubrics=deepcopy(RUBRICS))
    item = grounded(item, concept_id=concept.concept_id, locale=locale)
    item["difficulty_level"] = {"EASY": 1, "MEDIUM": 3, "HARD": 4}[difficulty]
    if locale == "vi":
        item["prompt"] = "Giải thích thao tác chọn cột kết quả bằng SELECT." if kind == "essay" else "Chọn cột kết quả bằng mệnh đề nào?" if kind == "mcq" else "Truy vấn tất cả mã định danh trong bảng đã cho."
        item["explanation"] = "SELECT xác định các cột kết quả; điều kiện WHERE lọc các hàng."
    payload = CandidateGenerateRequest(concept_id=concept.concept_id, question_type=kind,
                                      request_id=uuid4(), locale=locale, difficulty=difficulty)
    return admin, concept, payload, item


@pytest.mark.parametrize("kind,locale,difficulty", [("mcq", "en", "EASY"), ("mcq", "vi", "HARD"),
    ("sql", "en", "MEDIUM"), ("sql", "vi", "EASY"), ("essay", "en", "HARD"), ("essay", "vi", "MEDIUM")])
def test_all_formats_are_drafts_until_attested_approval(db_session, kind, locale, difficulty):
    admin, concept, payload, item = fixture(db_session, kind, locale, difficulty)
    runner = SandboxRunner(get_settings())
    seen = []
    candidates = generate_candidates(db_session, payload, admin, _service(db_session, {"questions": [item]}, seen=seen), runner)
    candidate = candidates[0]
    assert candidate.validation_status == "validated" and candidate.promoted_question_id is None
    assert db_session.query(Question).count() == 0
    assert seen[0]["response_format"]["type"] == "json_schema"
    assert seen[0]["max_tokens"] == 4096
    assert candidate.payload["source_refs"][0]["url"].startswith("https://www.postgresql.org/docs/17/")
    with pytest.raises(AppError, match="Review the current"):
        approve_candidate(db_session, candidate.candidate_id, admin, runner=runner)
    review = CandidateApprovalRequest(reviewed=True, content_hash=candidate.validation_detail["content_hash"])
    approved = approve_candidate(db_session, candidate.candidate_id, admin, review, runner)
    question = db_session.get(Question, approved.promoted_question_id)
    assert question.original_locale == locale and question.status == "validated"
    assert question.explanation == item["explanation"] and question.source_refs
    assert question.ai_review["human_review"]["reviewer_id"] == admin.account_id
    assert question.ai_review["human_review"]["content_hash"] == review.content_hash
    assert approve_candidate(db_session, candidate.candidate_id, admin, review, runner).promoted_question_id == question.question_id


def test_request_retry_is_idempotent_and_changed_intent_conflicts(db_session):
    admin, _, payload, item = fixture(db_session)
    seen = []
    service = _service(db_session, {"questions": [item]}, seen=seen)
    first = generate_candidates(db_session, payload, admin, service, None)
    again = generate_candidates(db_session, payload, admin, service, None)
    assert [r.candidate_id for r in first] == [r.candidate_id for r in again]
    assert len(seen) == 1 and db_session.query(QuestionCandidate).count() == 1
    with pytest.raises(AppError, match="different selections"):
        generate_candidates(db_session, payload.model_copy(update={"difficulty": "HARD"}), admin, service, None)
    assert len(seen) == 1


@pytest.mark.parametrize("change", ["source", "concept", "difficulty", "locale", "key", "duplicate_option", "empty", "objective"])
def test_invalid_candidates_never_create_drafts_or_cache(db_session, change):
    admin, _, payload, item = fixture(db_session)
    if change == "source": item["source_ids"] = ["fabricated-paper"]
    elif change == "concept": item["concept_id"] += 999
    elif change == "difficulty": item["difficulty_level"] = 5
    elif change == "locale": item["original_locale"] = "vi"
    elif change == "key": item["reference_answer"] = "B"
    elif change == "duplicate_option": item["options"][1]["option_text"] = "SELECT"
    elif change == "empty": item["explanation"] = ""
    else: item["objective_indices"] = [999]
    with pytest.raises(LLMError):
        generate_candidates(db_session, payload, admin, _service(db_session, {"questions": [item]}), None)
    assert db_session.query(QuestionCandidate).count() == 0
    assert db_session.query(LlmCache).count() == 0


def test_new_intent_duplicate_is_pending_and_cannot_be_approved(db_session):
    admin, _, payload, item = fixture(db_session)
    service = _service(db_session, {"questions": [item]})
    first = generate_candidates(db_session, payload, admin, service, None)[0]
    second = generate_candidates(db_session, payload.model_copy(update={"request_id": uuid4()}), admin, service, None)[0]
    assert first.candidate_id != second.candidate_id
    assert second.validation_status == "pending"
    with pytest.raises(AppError, match="pre-review checks"):
        approve_candidate(db_session, second.candidate_id, admin)
    assert db_session.query(Question).count() == 0


def test_metadata_and_stale_reviews_block_promotion(db_session):
    admin, concept, payload, item = fixture(db_session)
    candidate = generate_candidates(db_session, payload, admin, _service(db_session, {"questions": [item]}), None)[0]
    with pytest.raises(AppError, match="Review the current"):
        approve_candidate(db_session, candidate.candidate_id, admin, CandidateApprovalRequest(reviewed=True, content_hash="0" * 64))
    concept.description = "A different educational objective changes this concept's approved authoring context."
    db_session.commit()
    review = CandidateApprovalRequest(reviewed=True, content_hash=candidate.validation_detail["content_hash"])
    with pytest.raises(AppError, match="no longer pass"):
        approve_candidate(db_session, candidate.candidate_id, admin, review)
    assert validate_candidate(db_session, candidate.candidate_id, None).validation_status == "pending"
    assert db_session.query(Question).count() == 0


def test_missing_metadata_rejects_before_provider_and_rejection_has_actor(db_session):
    admin, concept, payload, item = fixture(db_session)
    concept.keywords = []
    db_session.commit()
    seen = []
    service = _service(db_session, {"questions": [item]}, seen=seen)
    with pytest.raises(AppError, match="keywords and learning objectives"):
        generate_candidates(db_session, payload, admin, service, None)
    assert seen == []
    concept.keywords = KEYWORDS
    db_session.commit()
    candidate = generate_candidates(db_session, payload, admin, service, None)[0]
    rejected = reject_candidate(db_session, candidate.candidate_id, admin)
    assert rejected.validation_status == "rejected"
    assert rejected.validation_detail["review"]["reviewer_id"] == admin.account_id
    repeated = reject_candidate(db_session, candidate.candidate_id, admin)
    assert repeated.validation_detail["review"] == rejected.validation_detail["review"]
    with pytest.raises(AppError, match="rejected draft"):
        validate_candidate(db_session, candidate.candidate_id, None)


def test_concurrent_same_request_creates_one_draft(db_session):
    admin, _, payload, item = fixture(db_session)
    seen = []
    def generate(_):
        with get_session_factory()() as db:
            return generate_candidates(db, payload, admin, _service(db, {"questions": [item]}, seen=seen), None)[0].candidate_id
    with ThreadPoolExecutor(max_workers=3) as executor:
        ids = list(executor.map(generate, range(3)))
    assert len(set(ids)) == 1 and len(seen) == 1


def test_metadata_changed_during_provider_call_cannot_create_a_stale_draft(db_session):
    import httpx
    import json
    from app.config import Settings
    from app.services.llm import ChatCompletionsProvider, LLMService
    from sqlalchemy import update
    admin, concept, payload, item = fixture(db_session)
    def response(_):
        with get_session_factory()() as concurrent:
            concurrent.execute(update(Concept).where(Concept.concept_id == concept.concept_id)
                               .values(description="The curriculum author changed this objective while generation was running."))
            concurrent.commit()
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"questions": [item]})}}]})
    settings = Settings(_env_file=None, llm_api_key="test-only", llm_base_url="https://provider.test/v1", llm_model="test-model")
    service = LLMService(settings, provider=ChatCompletionsProvider(settings.llm_base_url, settings.llm_api_key,
                         transport=httpx.MockTransport(response)), cache=None)
    with pytest.raises(AppError, match="concept changed during generation"):
        generate_candidates(db_session, payload, admin, service, None)
    assert db_session.query(QuestionCandidate).count() == 0


def test_concurrent_approval_is_idempotent_and_does_not_invent_reviewers(db_session):
    admin, _, payload, item = fixture(db_session)
    candidate = generate_candidates(db_session, payload, admin, _service(db_session, {"questions": [item]}), None)[0]
    review = CandidateApprovalRequest(reviewed=True, content_hash=candidate.validation_detail["content_hash"])
    def approve(_):
        with get_session_factory()() as db:
            return approve_candidate(db, candidate.candidate_id, admin, review).promoted_question_id
    with ThreadPoolExecutor(max_workers=3) as executor:
        ids = list(executor.map(approve, range(3)))
    assert len(set(ids)) == 1 and db_session.query(Question).count() == 1
    question = db_session.get(Question, ids[0])
    assert question.ai_review["human_review"]["reviewer_id"] == admin.account_id


@pytest.mark.parametrize("name,source", [("Normalization", "aalto-normalization"), ("Functional dependencies", "cmu-normalization"),
    ("Entity modeling", "mit-er"), ("Index design", "pg17-indexes"), ("Concurrency", "pg17-concurrency"),
    ("Query performance", "pg17-performance"), ("Server programming", "pg17-programming"),
    ("Client authentication", "pg17-security"), ("Data types", "pg17-types"), ("Window functions", "pg17-functions"),
    ("Database backup", "pg17-administration"), ("MVCC model: concurrency", "pg17-concurrency")])
def test_grounding_uses_relevant_verified_chapters(name, source):
    from types import SimpleNamespace
    from app.services.governed_generation import source_ids_for
    assert source in source_ids_for(SimpleNamespace(concept_code="TOPIC", concept_name=name, subject_area="PostgreSQL"))
