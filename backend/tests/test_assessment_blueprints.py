"""Competency-aligned assessment blueprint acceptance tests."""
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.errors import AppError
from app.models import (
    Assessment,
    AssessmentBlueprint,
    AssessmentConcept,
    AssessmentSession,
    Concept,
)
from app.repositories import AssessmentRepository
from app.schemas import PersonalizedStartRequest
from app.services import assessment_service
from app.services.blueprints import (
    resolve_blueprint,
    seed_blueprints,
    snapshot_policy,
)
from app.services.personalized_assessment import start_session

from test_adaptive_engine import (
    _complete_bank, _essay, _make_account, _mcq, _sql,
)

A6_THEORY = {
    "PostgreSQL Administration",
    "PostgreSQL Concurrency",
    "PostgreSQL Performance",
    "PostgreSQL Security",
    "PostgreSQL Server Programming",
}
A6_ALL = A6_THEORY | {
    "PostgreSQL Data Definition", "PostgreSQL Data Manipulation",
    "PostgreSQL Data Types", "PostgreSQL Functions", "PostgreSQL Querying",
}


def _concept(db, code, area, *, diff=1):
    concept = Concept(concept_code=code, concept_name=code, subject_area=area,
                      difficulty_level=diff)
    db.add(concept)
    db.flush()
    return concept


def _assessment(db, admin, concepts, *, title="Blueprint Test", max_q=13,
                mcq=10, sql=2, essay=1, min_d=1, max_d=5):
    assessment = Assessment(title=title, status="published",
                            created_by=admin.account_id, max_questions=max_q,
                            duration_min=60, target_mcq=mcq, target_sql=sql,
                            target_essay=essay)
    db.add(assessment)
    db.flush()
    for concept in concepts:
        db.add(AssessmentConcept(assessment_id=assessment.assessment_id,
                                 concept_id=concept.concept_id,
                                 min_difficulty=min_d, max_difficulty=max_d,
                                 target_pct=Decimal("60.00")))
    db.flush()
    return assessment


def _start(db, assessment, learner, concept_ids, difficulty="EASY"):
    return start_session(db, assessment.assessment_id, learner, SimpleNamespace(
        concept_ids=list(concept_ids), difficulty=difficulty,
        mode="FORMAL", question_count=13, request_id=uuid4()))


def _rows(db, assessment):
    return list(db.scalars(
        select(AssessmentBlueprint)
        .where(AssessmentBlueprint.assessment_id == assessment.assessment_id)
        .order_by(AssessmentBlueprint.subject_area, AssessmentBlueprint.difficulty_band,
                  AssessmentBlueprint.version_no)
    ))


def test_publish_seeds_every_area_and_band_and_is_idempotent(monkeypatch, db_session):
    admin = _make_account(db_session, "bp-admin@test.dev", "Administrator")
    concepts = [_concept(db_session, f"A6-{i}", area) for i, area in enumerate(sorted(A6_ALL))]
    assessment = _assessment(db_session, admin, concepts, max_q=13,
                             mcq=10, sql=2, essay=1, min_d=1, max_d=5)
    assessment.status = "draft"
    db_session.commit()

    monkeypatch.setattr(
        "app.services.assessment_validation.validate_assessment_bank",
        lambda *args, **kwargs: None,
    )
    assessment_service.set_assessment_status(
        db_session, assessment.assessment_id, "published", runner=object())

    rows = _rows(db_session, assessment)
    assert len(rows) == 30
    for row in rows:
        assert row.status == "approved" and row.version_no == 1
        assert row.target_mcq + row.target_sql + row.target_essay == row.max_questions
        if row.subject_area in A6_THEORY:
            assert (row.target_mcq, row.target_sql, row.target_essay) == (10, 0, 3)
            assert "structured_written" in row.evidence_types
        else:
            assert (row.target_mcq, row.target_sql, row.target_essay) == (10, 2, 1)

    before = len(rows)
    seed_blueprints(db_session, AssessmentRepository(db_session).get_assessment(assessment.assessment_id))
    db_session.commit()
    assert len(_rows(db_session, assessment)) == before


def test_a2_performance_uses_theory_evidence_at_eight_questions(db_session):
    admin = _make_account(db_session, "a2-admin@test.dev", "Administrator")
    concept = _concept(db_session, "A2-IDX", "Performance")
    assessment = _assessment(db_session, admin, [concept], max_q=8,
                             mcq=4, sql=2, essay=2, min_d=1, max_d=3)
    seed_blueprints(db_session, AssessmentRepository(db_session).get_assessment(
        assessment.assessment_id))
    db_session.commit()

    rows = _rows(db_session, assessment)
    assert {row.difficulty_band for row in rows} == {"EASY", "MEDIUM"}
    for row in rows:
        assert (row.target_mcq, row.target_sql, row.target_essay) == (6, 0, 2)
        assert row.max_questions == 8
        assert row.evidence_types == [
            "mcq_conceptual", "query_plan_and_index_reasoning", "structured_written"]


def test_representative_matrix_has_forty_nine_cells(db_session):
    admin = _make_account(db_session, "matrix-admin@test.dev", "Administrator")
    a2 = _assessment(db_session, admin, [
        _concept(db_session, "M-A2P", "Performance"),
        _concept(db_session, "M-A2Q", "Querying"),
    ], title="A2", max_q=8, mcq=4, sql=2, essay=2, min_d=1, max_d=3)
    a3 = _assessment(db_session, admin, [
        _concept(db_session, "M-A3D", "Database Design"),
        _concept(db_session, "M-A3Q", "SQL Querying"),
    ], title="A3")
    a4 = _assessment(db_session, admin, [
        _concept(db_session, "M-A4D", "Database Design"),
        _concept(db_session, "M-A4F", "SQL Foundations"),
        _concept(db_session, "M-A4Q", "SQL Querying"),
    ], title="A4")
    a6 = _assessment(db_session, admin, [
        _concept(db_session, f"M-A6-{i}", area) for i, area in enumerate(sorted(A6_ALL))
    ], title="A6")
    for assessment in (a2, a3, a4, a6):
        seed_blueprints(db_session, AssessmentRepository(db_session).get_assessment(
            assessment.assessment_id))
    db_session.commit()

    assert len(_rows(db_session, a2)) == 4
    assert len(_rows(db_session, a3)) == 6
    assert len(_rows(db_session, a4)) == 9
    assert len(_rows(db_session, a6)) == 30
    assert sum(len(_rows(db_session, a)) for a in (a2, a3, a4, a6)) == 49


def test_resolution_is_single_area_and_mixed_selection_falls_back(db_session):
    admin = _make_account(db_session, "resolve-admin@test.dev", "Administrator")
    perf = _concept(db_session, "R-PERF", "PostgreSQL Performance")
    query = _concept(db_session, "R-QUERY", "PostgreSQL Querying")
    assessment = _assessment(db_session, admin, [perf, query])
    seed_blueprints(db_session, AssessmentRepository(db_session).get_assessment(
        assessment.assessment_id))
    db_session.commit()
    assessment = AssessmentRepository(db_session).get_assessment(assessment.assessment_id)

    row, resolution = resolve_blueprint(db_session, assessment, [perf.concept_id], "EASY")
    assert resolution["mode"] == "blueprint"
    assert row.subject_area == "PostgreSQL Performance"
    assert (row.target_mcq, row.target_sql, row.target_essay) == (10, 0, 3)

    row, resolution = resolve_blueprint(db_session, assessment, [query.concept_id], "HARD")
    assert row.subject_area == "PostgreSQL Querying"
    assert (row.target_mcq, row.target_sql, row.target_essay) == (10, 2, 1)

    missing, resolution = resolve_blueprint(
        db_session, assessment, [perf.concept_id, query.concept_id], "EASY")
    assert missing is None
    assert resolution == {"mode": "legacy", "reason": "mixed_subject_areas"}


def test_versioning_appends_and_old_versions_are_immutable(db_session):
    admin = _make_account(db_session, "version-admin@test.dev", "Administrator")
    concept = _concept(db_session, "V-PERF", "PostgreSQL Performance")
    assessment = _assessment(db_session, admin, [concept])
    seed_blueprints(db_session, AssessmentRepository(db_session).get_assessment(
        assessment.assessment_id))
    db_session.commit()

    assessment = AssessmentRepository(db_session).get_assessment(assessment.assessment_id)
    first = [row for row in assessment.targets]  # keep target rows loaded
    assert first
    assessment.max_questions = 8
    assessment.target_mcq, assessment.target_sql, assessment.target_essay = 6, 0, 2
    db_session.flush()
    seed_blueprints(db_session, assessment)
    db_session.commit()

    rows = [row for row in _rows(db_session, assessment) if row.difficulty_band == "EASY"]
    assert [(row.version_no, row.target_mcq, row.target_sql, row.target_essay) for row in rows] == [
        (1, 10, 0, 3), (2, 6, 0, 2)]
    assessment = AssessmentRepository(db_session).get_assessment(assessment.assessment_id)
    resolved, resolution = resolve_blueprint(db_session, assessment, [concept.concept_id], "EASY")
    assert resolution["version_no"] == 2 and resolved.target_mcq == 6

    immutable_id = rows[0].blueprint_id
    with pytest.raises(DBAPIError, match="immutable"):
        db_session.execute(text(
            "UPDATE assessment_blueprint SET target_mcq = 1 WHERE blueprint_id = :id"),
            {"id": immutable_id})
        db_session.flush()
    db_session.rollback()
    assert db_session.get(AssessmentBlueprint, immutable_id).target_mcq == 10


def test_missing_and_retired_versions_are_actionable(db_session):
    admin = _make_account(db_session, "missing-admin@test.dev", "Administrator")
    concept = _concept(db_session, "X-PERF", "PostgreSQL Performance")
    assessment = _assessment(db_session, admin, [concept])
    db_session.add(AssessmentBlueprint(
        assessment_id=assessment.assessment_id, subject_area="PostgreSQL Performance",
        difficulty_band="EASY", version_no=1, status="approved", max_questions=13,
        target_mcq=10, target_sql=0, target_essay=3, scoring={}, evidence_types=[],
        approval_basis="fixture"))
    db_session.flush()
    db_session.commit()

    with pytest.raises(AppError) as exc:
        resolve_blueprint(db_session, assessment, [concept.concept_id], "MEDIUM")
    assert exc.value.code == "blueprint_not_available"
    assert exc.value.details["difficulty_band"] == "MEDIUM"

    db_session.add(AssessmentBlueprint(
        assessment_id=assessment.assessment_id, subject_area="PostgreSQL Performance",
        difficulty_band="EASY", version_no=2, status="retired", max_questions=13,
        target_mcq=10, target_sql=0, target_essay=3, scoring={}, evidence_types=[],
        approval_basis="fixture"))
    db_session.flush()
    with pytest.raises(AppError) as exc:
        resolve_blueprint(db_session, assessment, [concept.concept_id], "EASY")
    assert exc.value.code == "blueprint_retired"


def test_formal_start_captures_blueprint_and_schedules_no_sql(db_session):
    admin = _make_account(db_session, "start-admin@test.dev", "Administrator")
    learner = _make_account(db_session, "start-learner@test.dev", "Learner")
    concept = _concept(db_session, "S-PERF", "Performance")
    assessment = _assessment(db_session, admin, [concept], max_q=8,
                             mcq=4, sql=2, essay=2, min_d=1, max_d=3)
    for i in range(6):
        _mcq(db_session, concept, diff=1, admin=admin, prompt=f"Index concept {i}")
    for i in range(2):
        _essay(db_session, concept, diff=2, admin=admin)
    seed_blueprints(db_session, AssessmentRepository(db_session).get_assessment(
        assessment.assessment_id))
    db_session.commit()

    state = _start(db_session, assessment, learner, [concept.concept_id], "EASY")
    assert state.max_questions == 8
    assert state.current_question.question_type in {"mcq", "essay"}
    session = db_session.scalar(select(AssessmentSession).where(
        AssessmentSession.learner_id == learner.account_id))
    blueprint = db_session.scalar(select(AssessmentBlueprint).where(
        AssessmentBlueprint.blueprint_id == session.blueprint_id))
    assert blueprint is not None and blueprint.version_no == 1
    snapshot = session.config_snapshot
    assert snapshot["max_questions"] == 8
    assert (snapshot["target_mcq"], snapshot["target_sql"], snapshot["target_essay"]) == (6, 0, 2)
    assert snapshot["blueprint"] == snapshot_policy(blueprint)
    assert snapshot["blueprint_resolution"]["mode"] == "blueprint"
    assert snapshot["question_plan"]
    assert len(snapshot["question_plan"]) == 8
    assert all(item["question_type"] != "sql" for item in snapshot["question_plan"])


def test_insufficient_blueprint_inventory_never_substitutes(db_session):
    admin = _make_account(db_session, "short-admin@test.dev", "Administrator")
    learner = _make_account(db_session, "short-learner@test.dev", "Learner")
    concept = _concept(db_session, "SHORT-PERF", "Performance")
    assessment = _assessment(db_session, admin, [concept], max_q=8,
                             mcq=4, sql=2, essay=2, min_d=1, max_d=3)
    for i in range(5):
        _mcq(db_session, concept, diff=1, admin=admin, prompt=f"Short concept {i}")
    for i in range(2):
        _essay(db_session, concept, diff=2, admin=admin)
    seed_blueprints(db_session, AssessmentRepository(db_session).get_assessment(
        assessment.assessment_id))
    db_session.commit()

    with pytest.raises(AppError) as exc:
        _start(db_session, assessment, learner, [concept.concept_id], "EASY")
    assert exc.value.code == "insufficient_question_pool"
    assert exc.value.details["required_by_type"]["mcq"] == 6
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 0


def test_mixed_formal_start_keeps_published_legacy_mix(db_session):
    admin = _make_account(db_session, "mixed-admin@test.dev", "Administrator")
    learner = _make_account(db_session, "mixed-learner@test.dev", "Learner")
    perf = _concept(db_session, "MIX-PERF", "Performance")
    query = _concept(db_session, "MIX-QUERY", "SQL Querying")
    assessment = _assessment(db_session, admin, [perf, query], max_q=13,
                             mcq=10, sql=2, essay=1)
    _complete_bank(db_session, admin, [perf, query], 1, 5)
    for i in range(3):
        _mcq(db_session, perf if i % 2 == 0 else query, diff=3, admin=admin,
             prompt=f"Medium mix MCQ {i}")
    for concept in (perf, query):
        _sql(db_session, concept, diff=3, admin=admin)
    seed_blueprints(db_session, AssessmentRepository(db_session).get_assessment(
        assessment.assessment_id))
    db_session.commit()

    state = _start(db_session, assessment, learner,
                   [perf.concept_id, query.concept_id], "MEDIUM")
    assert state.max_questions == 13
    session = db_session.scalar(select(AssessmentSession).where(
        AssessmentSession.learner_id == learner.account_id))
    assert session.blueprint_id is None
    snapshot = session.config_snapshot
    assert (snapshot["target_mcq"], snapshot["target_sql"], snapshot["target_essay"]) == (10, 2, 1)
    assert snapshot["blueprint_resolution"] == {
        "mode": "legacy", "reason": "mixed_subject_areas"}
    assert Counter(item["question_type"] for item in snapshot["question_plan"]) == {
        "mcq": 10, "sql": 2, "essay": 1}


def test_unmanaged_assessment_keeps_legacy_behavior(db_session):
    admin = _make_account(db_session, "legacy-admin@test.dev", "Administrator")
    concept = _concept(db_session, "LEGACY", "SQL Querying")
    assessment = _assessment(db_session, admin, [concept])
    db_session.commit()

    row, resolution = resolve_blueprint(db_session, assessment, [concept.concept_id], "EASY")
    assert row is None
    assert resolution == {"mode": "legacy", "reason": "assessment_not_blueprint_managed"}


def test_learners_cannot_supply_blueprint_configuration():
    with pytest.raises(ValidationError):
        PersonalizedStartRequest(
            concept_ids=[1], difficulty="EASY", request_id=str(uuid4()),
            mode="FORMAL", question_count=13, target_mcq=5)
    with pytest.raises(ValidationError):
        PersonalizedStartRequest(
            concept_ids=[1], difficulty="EASY", request_id=str(uuid4()),
            mode="FORMAL", question_count=13, blueprint_id=7)


def test_deleting_assessment_removes_blueprints_and_keeps_referenced_versions(db_session):
    """Versions referenced by a session snapshot can never cascade away."""
    admin = _make_account(db_session, "delete-admin@test.dev", "Administrator")
    concept = _concept(db_session, "DEL-PERF", "PostgreSQL Performance")
    assessment = _assessment(db_session, admin, [concept])
    seed_blueprints(db_session, AssessmentRepository(db_session).get_assessment(
        assessment.assessment_id))
    db_session.commit()

    # No session exists, so the whole assessment (and its versions) is removable.
    assessment_service.delete_assessment(db_session, assessment.assessment_id)
    assert db_session.get(Assessment, assessment.assessment_id) is None
    assert db_session.scalar(select(func.count()).select_from(AssessmentBlueprint).where(
        AssessmentBlueprint.assessment_id == assessment.assessment_id)) == 0

    # A session that binds one version makes the assessment undeletable and the
    # version rows remain exactly as captured.
    second = _assessment(db_session, admin, [_concept(db_session, "DEL-KEEP", "SQL Querying")])
    seed_blueprints(db_session, AssessmentRepository(db_session).get_assessment(
        second.assessment_id))
    db_session.commit()
    captured = db_session.scalar(
        select(AssessmentBlueprint).where(
            AssessmentBlueprint.assessment_id == second.assessment_id,
            AssessmentBlueprint.subject_area == "SQL Querying",
            AssessmentBlueprint.difficulty_band == "EASY"))
    db_session.add(AssessmentSession(
        assessment_id=second.assessment_id, learner_id=admin.account_id, status="in_progress",
        expires_at=datetime.now(timezone.utc), blueprint_id=captured.blueprint_id,
        config_snapshot={}))
    db_session.commit()
    with pytest.raises(AppError, match="Assessment has sessions"):
        assessment_service.delete_assessment(db_session, second.assessment_id)
    rows = _rows(db_session, AssessmentRepository(db_session).get_assessment(
        second.assessment_id))
    assert [(row.version_no, row.target_mcq, row.target_sql, row.target_essay)
            for row in rows] == [(1, 10, 2, 1)] * 3
    assert db_session.get(AssessmentBlueprint, captured.blueprint_id) is not None
