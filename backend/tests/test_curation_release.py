"""Human review boundaries and concurrent curriculum writes."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models import CloConcept, ConceptDependency, QuestionConcept
from app.schemas import QuestionAiReviewRequest, QuestionUpsertRequest
from app.services import ai_admin_service as ai, curriculum_service as curriculum
from app.services import concept_graph_service as graph, question_service as questions
from test_ai_admin import _make_account, _concept, _clo, _mcq_question
from test_llm_release import _service


def _setup(db):
    admin = _make_account(db, "review@test.dev", "Administrator")
    concept = _concept(db, "SQL-REVIEW")
    question = _mcq_question(db, admin)
    db.commit()
    return admin, concept, question


@pytest.mark.parametrize("invalid", [{"prompt": 42}, {"options": [42]},
    {"options": {}}, {"options": [{"option_label": "A", "option_text": 42, "is_correct": True}]},
    {"datasets": [None]}, {"rubrics": ["Partial"]}, {"points": "NaN"},
    {"points": True}, {"points": -1}, {"points": 1000}])
def test_malformed_candidate_is_rejected_before_caching(db_session, invalid):
    from app.models import LlmCache
    from app.services.llm import LLMError
    service = _service(db_session, {"questions": [{
        "prompt": "Explain a key", "difficulty_level": 1,
        "options": [{"option_label": "A", "option_text": "Unique", "is_correct": True},
                    {"option_label": "B", "option_text": "Nullable", "is_correct": False}],
        **invalid,
    }]})
    with pytest.raises(LLMError):
        service.generate_structured("generate", [],
            validator=lambda result: ai._validate_ai_payload(result, "generate", "mcq"))
    assert db_session.query(LlmCache).count() == 0


@pytest.mark.parametrize("decision", ["confirmed", "rejected"])
def test_difficulty_and_criteria_need_explicit_review(db_session, decision):
    _, concept, question = _setup(db_session)
    ai.suggest_question_tags(db_session, question.question_id, _service(db_session, {
        "concept_ids": [concept.concept_id], "difficulty_level": 4,
        "evaluation_criteria": "Explain the uniqueness constraint",
    }))
    assert question.difficulty_level == 1
    assert question.ai_review["status"] == "pending"
    detail = questions.get_question(db_session, question.question_id)
    payload = QuestionUpsertRequest(**{
        **detail.model_dump(), "prompt": "Unrelated wording edit",
        "concept_ids": [concept.concept_id], "required_concept_ids": [],
    })
    updated = questions.replace_question(db_session, question.question_id, payload)
    assert updated.concepts[0].confirmed is False
    assert updated.ai_review["status"] == "pending"
    result = ai.review_question_suggestion(db_session, question.question_id,
        QuestionAiReviewRequest(decision=decision, apply_difficulty=True))
    assert result.ai_review["status"] == decision
    assert result.difficulty_level == (4 if decision == "confirmed" else 1)
    assert result.concepts[0].confirmed is False
    with pytest.raises(AppError):
        ai.review_question_suggestion(db_session, question.question_id,
            QuestionAiReviewRequest(decision="confirmed"))


@pytest.mark.parametrize("status", ["pending", "rejected"])
def test_generic_clo_set_does_not_approve_ai_mapping(db_session, status):
    admin, concept, _ = _setup(db_session)
    clo = _clo(db_session, admin)
    db_session.add(CloConcept(clo_id=clo.clo_id, concept_id=concept.concept_id,
                              mapping_source="ai", status=status))
    db_session.commit()
    result = curriculum.set_clo_concepts(db_session, clo.clo_id, [concept.concept_id])
    assert result.concepts[0].status == status
    assert ai.confirm_clo_link(db_session, clo.clo_id, concept.concept_id).concepts[0].status == "confirmed"


def test_rejected_question_tag_survives_generic_edit(db_session):
    _, concept, question = _setup(db_session)
    db_session.add(QuestionConcept(question_id=question.question_id, concept_id=concept.concept_id,
                                   tag_source="ai", confirmed=False))
    db_session.commit()
    ai.reject_question_tag(db_session, question.question_id, concept.concept_id)
    detail = questions.get_question(db_session, question.question_id)
    payload = QuestionUpsertRequest(**{**detail.model_dump(), "concept_ids": [concept.concept_id]})
    result = questions.replace_question(db_session, question.question_id, payload)
    assert result.concepts[0].review_status == "rejected"
    assert result.concepts[0].confirmed is False


def test_untouched_prerequisite_save_preserves_edge(db_session):
    _, a, _ = _setup(db_session)
    b = _concept(db_session, "SQL-DEPENDENT")
    db_session.commit()
    graph.set_concept_prerequisites(db_session, b.concept_id, [a.concept_id])
    edge = db_session.get(ConceptDependency, (b.concept_id, a.concept_id))
    created = edge.created_at
    graph.set_concept_prerequisites(db_session, b.concept_id, [a.concept_id])
    assert db_session.get(ConceptDependency, (b.concept_id, a.concept_id)).created_at == created


def test_concurrent_opposing_edges_cannot_form_cycle(db_session):
    _, a, _ = _setup(db_session)
    b = _concept(db_session, "SQL-CONCURRENT")
    db_session.commit()
    ids = a.concept_id, b.concept_id
    barrier = Barrier(2)
    def write(pair):
        with Session(db_session.bind) as db:
            barrier.wait()
            try:
                graph.set_concept_prerequisites(db, pair[0], [pair[1]])
                return "saved"
            except AppError as error:
                db.rollback()
                return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(write, [ids, tuple(reversed(ids))]))
    assert sorted(results) == ["dependency_cycle", "saved"]
    assert db_session.query(ConceptDependency).count() == 1
