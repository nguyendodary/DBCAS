"""Exact formulas, evidence provenance and dimension deduplication."""
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace as Record

import pytest

from app.models import Account, CloConcept, CourseLearningOutcome
from app.repositories import AssessmentRepository, QuestionRepository
from app.services.competency_dimensions import Evidence, extract_evidence, rank_learners, summarize
from app.services.evidence_context import capture_question
from sqlalchemy import select
from test_admin_questions import _admin, _concept, _mcq_payload


def sample(attempt_id=1, learner_id=1):
    return Evidence(attempt_id, 1, learner_id, Decimal(8), Decimal(10), 1,
                    ("SQL", "SQL"), (("1", "CLO1"), ("1", "CLO1")), True)


def test_points_weighted_dimensions_and_no_duplicate_contributions():
    first = sample()
    second = Evidence(2, 1, 1, Decimal(1), Decimal(2), 3, ("Index",), (("2", "CLO2"),), True)
    result = summarize([first, first, second])
    assert result["overall"]["competency_pct"] == Decimal("75.00")
    assert result["overall"]["evidence_count"] == 2
    assert [(r["label"], r["competency_pct"], r["rank"]) for r in result["topics"]] == [
        ("SQL", Decimal("80.00"), 1), ("Index", Decimal("50.00"), 2)]
    assert result["clos"][0]["points_possible"] == 10
    assert result["difficulties"][1]["key"] == "3"
    empty = summarize([])
    assert empty["overall"]["competency_pct"] is None and empty["clos"] == []


def test_rounding_ranks_and_invalid_evidence():
    rows = [replace(sample(), earned=Decimal(1), possible=Decimal(3)),
            replace(sample(2, 2), earned=Decimal(1), possible=Decimal(3)),
            replace(sample(3, 3), earned=Decimal(1), possible=Decimal(4))]
    assert [r["rank"] for r in rank_learners(rows)] == [1, 1, 3]
    assert rank_learners(rows)[0]["competency_pct"] == Decimal("33.33")
    assert [(r["rank"], r["learner_id"]) for r in rank_learners(rows[:1])] == [(1, rows[0].learner_id)]
    with pytest.raises(ValueError):
        replace(sample(), earned=Decimal("NaN"))
    with pytest.raises(ValueError):
        summarize([sample(), replace(sample(), earned=Decimal(9))])


def test_publication_practice_pending_and_unknown_historical_clos():
    session = Record(session_id=1, learner_id=1, status="completed", release_status="published", config_snapshot={})
    question = Record(points=Decimal(10), difficulty_level=1, concept_tags=[])
    attempt = Record(attempt_id=1, submitted_at=1, score=Decimal(8), grading_status="graded",
                     question_snapshot=None, question=question)
    assert summarize(extract_evidence([session], {1: [attempt]}))["clo_mapping_unknown_attempts"] == 1
    session.release_status = "pending_review"
    assert extract_evidence([session], {1: [attempt]}) == []
    session.release_status = "published"
    session.config_snapshot = {"assembly_mode": "PRACTICE"}
    assert extract_evidence([session], {1: [attempt]}) == []
    session.config_snapshot = {}
    attempt.grading_status = "pending"
    assert extract_evidence([session], {1: [attempt]}) == []


def test_new_snapshots_capture_confirmed_clos_and_preserve_old_mapping(client, db_session):
    headers = _admin(client, db_session)
    concept = _concept(db_session, "DN-CLO-SNAPSHOT")
    admin_id = db_session.scalar(select(Account.account_id))
    clo = CourseLearningOutcome(clo_code="DN-CLO", title="SQL", created_by=admin_id)
    db_session.add(clo)
    db_session.flush()
    link = CloConcept(clo_id=clo.clo_id, concept_id=concept.concept_id, status="confirmed")
    db_session.add(link)
    db_session.commit()
    qid = client.post("/api/v1/admin/questions", headers=headers, json=_mcq_payload(concept.concept_id)).json()["question_id"]
    repo = AssessmentRepository(db_session)
    question = QuestionRepository(db_session).get_detail(qid)
    snapshot = capture_question(repo, question)
    assert snapshot["clo_mappings"][0]["clo_code"] == "DN-CLO"
    link.status = "pending"
    db_session.commit()
    assert capture_question(repo, question)["clo_mappings"] == []
    assert snapshot["clo_mappings"][0]["clo_code"] == "DN-CLO"
