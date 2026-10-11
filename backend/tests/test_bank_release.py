"""Formal bank acceptance, real fixture execution and immutable versions."""
import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.benchmark import import_pack
from app.config import ROOT_DIR, get_settings
from app.errors import AppError
from app.models import Assessment, Question, SqlTestDataset, Concept, ConceptDependency, CloConcept, CourseLearningOutcome
from app.repositories import AssessmentRepository
from app.schemas import AssessmentUpsertRequest, QuestionUpsertRequest
from app.services import assessment_service as assessments, question_service as questions
from app.services.adaptive_engine import start_session
from app.services.bank_validation import sql_fixture_problems
from app.services.sandbox_runner import SandboxRunner
from test_ai_admin import _make_account
from test_draft_lifecycle import _fixture


@pytest.mark.parametrize("field,value", [("duration_min",30),("max_questions",12),
    ("target_mcq",9),("target_sql",3),("target_essay",0),("target_essay",True)])
def test_nonformal_assessment_configuration_rejected(field, value):
    with pytest.raises(ValidationError):
        AssessmentUpsertRequest(title="Invalid alternative", concepts=[{"concept_id":1,"target_pct":60}], **{field:value})


def _pack():
    return json.loads((ROOT_DIR / "db/benchmark_pack.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("change", ["single_dataset", "no_edge", "expected", "unsafe_setup", "missing_technique", "unsupported_technique"])
def test_invalid_sql_configuration_is_a_bank_error(change):
    item = next(q for q in _pack()["questions"] if q["key"] == "sql-sql-join")
    datasets = [SimpleNamespace(**d) for d in item["datasets"]]
    required = ["join"]
    if change == "single_dataset": datasets = datasets[:1]
    if change == "no_edge": datasets[1].is_edge_case = False
    if change == "expected": datasets[0].expected_result = {"rows": [[1], [1, 2]]}
    if change == "unsafe_setup": datasets[0].setup_sql = "CREATE FUNCTION evil() RETURNS int AS 'SELECT 1' LANGUAGE SQL"
    if change == "missing_technique": item["reference_answer"] = "SELECT id FROM sales"
    if change == "unsupported_technique": required = [None]
    assert sql_fixture_problems(datasets, item["reference_answer"], required)


def test_reviewed_benchmark_import_is_repeatable_and_supports_formal_session(db_session):
    admin = _make_account(db_session, "benchmark-admin@test.dev", "Administrator")
    runner = SandboxRunner(get_settings())
    first = import_pack(db_session, admin, runner)
    second = import_pack(db_session, admin, runner)
    assert first == second
    assert len(first["concept_ids"]) == 12 and len(first["question_ids"]) == 19
    learner = _make_account(db_session, "benchmark-learner@test.dev", "Learner")
    state = start_session(db_session, first["assessment_ids"][0], learner)
    assert state.max_questions == 13
    assert state.current_question.question_type == "mcq"
    assert state.current_question.difficulty_level <= 2
    assert state.expires_at - state.started_at <= __import__('datetime').timedelta(minutes=60)


def test_real_sql_reference_mismatch_is_rejected_before_validation(db_session):
    admin = _make_account(db_session, "benchmark-admin@test.dev", "Administrator")
    result = import_pack(db_session, admin, SandboxRunner(get_settings()))
    question = db_session.scalar(select(Question).where(Question.question_type == "sql"))
    dataset = db_session.scalar(select(SqlTestDataset).where(SqlTestDataset.question_id == question.question_id))
    dataset.expected_result = {"columns": ["id", "amount"], "rows": [[99, 99]], "check_columns": True}
    question.status = "draft"
    db_session.commit()
    with pytest.raises(AppError) as error:
        questions.set_question_status(db_session, question.question_id, "validated", SandboxRunner(get_settings()))
    assert error.value.code == "question_incomplete"
    assert db_session.get(Question, question.question_id).status == "draft"


def test_benchmark_import_preserves_existing_edges_and_pending_mappings(db_session):
    admin = _make_account(db_session, "benchmark-admin@test.dev", "Administrator")
    runner = SandboxRunner(get_settings())
    result = import_pack(db_session, admin, runner)
    extra = Concept(concept_code="EXTRA", concept_name="Extra", subject_area="SQL Querying", difficulty_level=1)
    db_session.add(extra)
    db_session.flush()
    cid = result["concept_ids"]["SQL-SELECT"]
    clo = db_session.scalar(select(CourseLearningOutcome))
    db_session.add(ConceptDependency(concept_id=cid, prerequisite_concept_id=extra.concept_id))
    db_session.add(CloConcept(clo_id=clo.clo_id, concept_id=extra.concept_id, mapping_source="ai", status="pending"))
    db_session.commit()
    assert import_pack(db_session, admin, runner) == result
    assert db_session.get(ConceptDependency, (cid, extra.concept_id)) is not None
    assert db_session.get(CloConcept, (clo.clo_id, extra.concept_id)).status == "pending"


def test_benchmark_import_rejects_different_content_under_the_same_prompt(db_session):
    admin = _make_account(db_session, "benchmark-admin@test.dev", "Administrator")
    runner = SandboxRunner(get_settings())
    result = import_pack(db_session, admin, runner)
    question = db_session.get(Question, result["question_ids"][0])
    question.points = 2
    db_session.commit()
    with pytest.raises(AppError) as error:
        import_pack(db_session, admin, runner)
    assert error.value.code == "benchmark_question_conflict"
    assert db_session.get(Question, question.question_id).points == 2


def test_benchmark_missing_sql_metadata_requires_explicit_additive_opt_in(db_session):
    admin = _make_account(db_session, "benchmark-admin@test.dev", "Administrator")
    concept = Concept(concept_code="SQL-SELECT", concept_name="Existing SELECT", subject_area="SQL Querying", difficulty_level=1)
    db_session.add(concept)
    db_session.commit()
    runner = SandboxRunner(get_settings())
    with pytest.raises(AppError) as error:
        import_pack(db_session, admin, runner)
    assert error.value.code == "benchmark_concept_conflict"
    assert concept.sql_feature is None
    result = import_pack(db_session, admin, runner, fill_missing_techniques=True)
    assert result["concept_ids"]["SQL-SELECT"] == concept.concept_id
    assert concept.sql_feature == "select" and concept.concept_name == "Existing SELECT"


def test_editing_used_mcq_creates_version_and_preserves_old_option_ids(db_session):
    _, session, attempt, question, _, _, _ = _fixture(db_session)
    old_options = [o.option_id for o in question.options]
    detail = questions.get_question(db_session, question.question_id)
    payload = QuestionUpsertRequest(**{**detail.model_dump(), "prompt": "Revised prompt",
        "concept_ids": [t.concept_id for t in detail.concepts], "points": 2})
    edited = questions.replace_question(db_session, question.question_id, payload)
    assert edited.question_id != question.question_id and edited.family_id == question.question_id
    assert edited.version_no == 2 and edited.status == "draft"
    assert question.prompt == "Original prompt" and str(question.points) == "1.00"
    assert [o.option_id for o in question.options] == old_options
    assert attempt.question_id == question.question_id


def test_redrafting_closed_assessment_creates_new_configuration(db_session):
    _, session, _, question, concept, _, _ = _fixture(db_session)
    original = db_session.get(Assessment, session.assessment_id)
    original.status = "closed"
    db_session.commit()
    result = assessments.set_assessment_status(db_session, original.assessment_id, "draft")
    assert result.assessment_id != original.assessment_id
    assert original.status == "closed" and session.assessment_id == original.assessment_id
    cloned = AssessmentRepository(db_session).get_assessment(result.assessment_id)
    assert cloned.family_id == original.assessment_id and cloned.version_no == 2
    assert [t.concept_id for t in cloned.targets] == [concept.concept_id]


@pytest.mark.parametrize("condition", ["valid", "wrong_expected", "unsafe_setup"])
def test_sql_candidate_real_service_validates_before_cache_and_preserves_points(db_session, condition):
    from app.models import Concept, LlmCache, QuestionCandidate
    from app.schemas import CandidateGenerateRequest
    from app.services.ai_admin_service import generate_candidates, approve_candidate
    from app.services.llm import LLMError
    from test_llm_release import _service
    admin = _make_account(db_session, "candidate-admin@test.dev", "Administrator")
    concept = Concept(concept_code="SQL-SELECT", concept_name="SELECT", subject_area="SQL Querying", sql_feature="select")
    db_session.add(concept)
    db_session.commit()
    item = next(q for q in _pack()["questions"] if q["key"] == "sql-sql-select")
    if condition == "wrong_expected":
        item["datasets"][0]["expected_result"]["rows"] = [[999, 999]]
    elif condition == "unsafe_setup":
        item["datasets"][0]["setup_sql"] = "CREATE EXTENSION dblink"
    call = lambda: generate_candidates(db_session, CandidateGenerateRequest(
        concept_id=concept.concept_id, question_type="sql", count=1), admin,
        _service(db_session, {"questions": [item]}), SandboxRunner(get_settings()))
    if condition != "valid":
        with pytest.raises(LLMError): call()
        assert db_session.query(LlmCache).count() == 0
        assert db_session.query(QuestionCandidate).count() == 0
    else:
        result = call()[0]
        assert result.validation_status == "validated" and result.promoted_question_id is None
        approved = approve_candidate(db_session, result.candidate_id, admin)
        assert db_session.get(Question, approved.promoted_question_id).points == 5
        assert db_session.query(LlmCache).count() == 1
