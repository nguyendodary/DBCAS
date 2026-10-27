"""Supervisor acceptance, real database integration and confidentiality gates."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from itertools import combinations
from decimal import Decimal
from random import Random
from types import SimpleNamespace as Row
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text

from app.config import get_settings
from app.db import get_session_factory
from app.deps import get_llm_service
from app.errors import AppError
from app.main import app
from app.models import AssessmentSession, Attempt, GradeReview, GradingJob, Question, ResultReleaseEvent, AccountRole, Role
from app.repositories import AssessmentRepository
from app.schemas import PersonalizedStartRequest
from app.security import create_access_token
from app.services.cumulative_competency import aggregate_sessions
from app.services.personalized_assessment import select_questions, start_session
from test_adaptive_engine import _make_account, _concept, _mcq, _sql, _essay, _assessment
from test_draft_lifecycle import _essay_service
from test_draft_lifecycle import _fixture


def headers(account, role="Learner"):
    token, _ = create_access_token(account.account_id, [role], get_settings())
    return {"Authorization": f"Bearer {token}"}


def bank(db, *, difficulty=1, policy="IMMEDIATE", skills=2):
    admin = _make_account(db, "supervisor-admin@test.dev", "Administrator")
    learner = _make_account(db, "supervisor-learner@test.dev", "Learner")
    concepts = [_concept(db, f"SKILL-{i}") for i in range(skills)]
    for c in concepts:
        for i in range(12):
            _mcq(db, c, diff=difficulty, admin=admin, prompt=f"{c.concept_code} item {i}")
        for _ in range(3):
            _sql(db, c, diff=difficulty, admin=admin)
        for _ in range(2):
            _essay(db, c, diff=difficulty, admin=admin)
    a = _assessment(db, admin, concepts, complete=False)
    a.result_release_policy = policy
    db.commit()
    return admin, learner, concepts, a


def selection(concepts, difficulty="EASY"):
    return {"concept_ids": [c.concept_id for c in concepts], "difficulty": difficulty, "request_id": str(uuid4())}


def started(client, db, *, difficulty=1, policy="IMMEDIATE", skills=2):
    admin, learner, concepts, assessment = bank(db, difficulty=difficulty, policy=policy, skills=skills)
    label = "EASY" if difficulty <= 2 else "MEDIUM" if difficulty == 3 else "HARD"
    payload = selection(concepts, label)
    response = client.post(f"/api/v1/assessments/{assessment.assessment_id}/sessions", headers=headers(learner), json=payload)
    assert response.status_code == 201, response.json()
    return admin, learner, concepts, assessment, response.json(), payload


def complete(client, db, learner, state, *, llm_available=True):
    if llm_available:
        app.dependency_overrides[get_llm_service] = lambda: _essay_service(db)
    try:
        while state["current_question"]:
            q = state["current_question"]
            attempt = db.get(Attempt, q["attempt_id"])
            snap = attempt.question_snapshot
            answer = {"question_id": q["question_id"]}
            if q["question_type"] == "mcq":
                answer["selected_option_id"] = next(o["option_id"] for o in snap["options"] if o["is_correct"])
            elif q["question_type"] == "sql":
                answer["sql_answer"] = "SELECT 1"
            else:
                answer["essay_answer"] = "3NF"
            result = client.post(f"/api/v1/sessions/{state['session_id']}/submit", headers=headers(learner), json=answer)
            assert result.status_code == 200, result.json()
            if state["result_release_policy"] == "HUMAN_VERIFIED":
                assert result.json()["answer"]["score"] is None
                assert result.json()["answer"]["is_correct"] is None
            state = result.json()["state"]
        result = client.post(f"/api/v1/sessions/{state['session_id']}/finish", headers=headers(learner))
        assert result.status_code == 200, result.json()
        return result.json()
    finally:
        app.dependency_overrides.pop(get_llm_service, None)


@pytest.mark.parametrize("level,label", [(1, "EASY"), (2, "EASY"), (3, "MEDIUM"), (4, "HARD"), (5, "HARD")])
def test_personalized_band_coverage_quotas_and_frozen_plan(client, db_session, level, label):
    _, learner, concepts, assessment, state, payload = started(client, db_session, difficulty=level)
    session = db_session.get(AssessmentSession, state["session_id"])
    config = session.config_snapshot
    assert config["selected_concept_ids"] == sorted(c.concept_id for c in concepts)
    assert config["difficulty"] == label
    assert len(config["question_ids"]) == len(set(config["question_ids"])) == 13
    assert Counter(q["question_type"] for q in config["question_plan"]) == {"mcq": 10, "sql": 2, "essay": 1}
    assert {q["difficulty_level"] for q in config["question_plan"]} == {level}
    assert set(config["selected_concept_ids"]) <= {c["concept_id"] for q in config["question_plan"] for c in q["concepts"]}
    assert "question_plan" not in state and "question_ids" not in state
    assert "is_correct" not in str(state) and "reference_answer" not in str(state)
    retry = client.post(f"/api/v1/assessments/{assessment.assessment_id}/sessions", headers=headers(learner), json=payload)
    assert retry.json()["session_id"] == state["session_id"]
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 1


@pytest.mark.parametrize("change,code", [({"difficulty": "IMPOSSIBLE"}, "validation_error"),
    ({"concept_ids": []}, "validation_error"), ({"concept_ids": [999999]}, "invalid_skill_selection"),
    ({"concept_ids": [True]}, "validation_error"), ({"score": 100}, "validation_error")])
def test_invalid_selection_rejected_without_session(client, db_session, change, code):
    _, learner, concepts, a = bank(db_session)
    result = client.post(f"/api/v1/assessments/{a.assessment_id}/sessions", headers=headers(learner), json={**selection(concepts), **change})
    assert result.status_code == 422 and result.json()["error"]["code"] == code
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 0


def test_duplicate_skills_and_insufficient_difficulty_rejected(client, db_session):
    _, learner, concepts, a = bank(db_session)
    for payload, code in [({**selection(concepts), "concept_ids": [concepts[0].concept_id] * 2}, "duplicate_concept_ids"),
                          (selection(concepts, "HARD"), "insufficient_question_pool")]:
        result = client.post(f"/api/v1/assessments/{a.assessment_id}/sessions", headers=headers(learner), json=payload)
        assert result.status_code == 422 and result.json()["error"]["code"] == code
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 0


def test_single_skill_selection_and_ineligible_bank_questions(client, db_session):
    admin, learner, concepts, a = bank(db_session)
    hidden = _mcq(db_session, concepts[0], admin=admin, status="draft")
    unconfirmed = _mcq(db_session, concepts[0], admin=admin, confirmed=False)
    db_session.commit()
    result = client.post(f"/api/v1/assessments/{a.assessment_id}/sessions", headers=headers(learner), json=selection(concepts[:1]))
    assert result.status_code == 201
    snap = db_session.get(AssessmentSession, result.json()["session_id"]).config_snapshot
    assert {c["concept_id"] for q in snap["question_plan"] for c in q["concepts"]} == {concepts[0].concept_id}
    assert not {hidden.question_id, unconfirmed.question_id} & set(snap["question_ids"])


def test_concurrent_repeated_starts_and_changed_request_conflict(client, db_session):
    _, learner, concepts, a = bank(db_session)
    payload = PersonalizedStartRequest(**selection(concepts))
    def create(_):
        with get_session_factory()() as db:
            return start_session(db, a.assessment_id, learner, payload).session_id
    with ThreadPoolExecutor(max_workers=4) as executor:
        ids = list(executor.map(create, range(4)))
    assert len(set(ids)) == 1
    different = payload.model_copy(update={"difficulty": "HARD"})
    result = client.post(f"/api/v1/assessments/{a.assessment_id}/sessions", headers=headers(learner), json=different.model_dump(mode="json"))
    assert result.status_code == 409 and result.json()["error"]["code"] == "start_request_conflict"


@pytest.mark.parametrize("change", ["skill_coverage", "version_family"])
def test_curation_between_selection_and_snapshot_cannot_invalidate_plan(client, db_session, monkeypatch, change):
    from app.services import personalized_assessment

    _, learner, concepts, assessment = bank(db_session)
    original_select = personalized_assessment.select_questions

    def curate_before_locks(*args, **kwargs):
        chosen = original_select(*args, **kwargs)
        with get_session_factory()() as curator:
            if change == "skill_coverage":
                from app.models import QuestionConcept
                curator.execute(QuestionConcept.__table__.update().where(
                    QuestionConcept.question_id.in_([q.question_id for q in chosen]),
                    QuestionConcept.concept_id == concepts[1].concept_id,
                ).values(concept_id=concepts[0].concept_id))
            else:
                revision = curator.get(Question, chosen[1].question_id)
                revision.family_id = chosen[0].family_id or chosen[0].question_id
                revision.version_no = 2
            curator.commit()
        return chosen

    monkeypatch.setattr(personalized_assessment, "select_questions", curate_before_locks)
    result = client.post(f"/api/v1/assessments/{assessment.assessment_id}/sessions",
                         headers=headers(learner), json=selection(concepts))
    assert result.status_code == 409 and result.json()["error"]["code"] == "question_bank_changed"
    assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 0


def test_plan_and_resume_survive_question_and_concept_mutation(client, db_session):
    _, learner, concepts, _, state, _ = started(client, db_session)
    session = db_session.get(AssessmentSession, state["session_id"])
    original_plan = session.config_snapshot["question_plan"]
    current = state["current_question"]
    future = next(q for q in original_plan[1:] if q["question_type"] == "mcq")
    q = db_session.get(Question, future["question_id"])
    q.prompt = "Changed after starting"
    q.points = Decimal(50)
    q.status = "retired"
    concepts[0].concept_name = "Edited topic"
    db_session.commit()
    assert client.get(f"/api/v1/sessions/{session.session_id}", headers=headers(learner)).json()["current_question"] == current
    complete(client, db_session, learner, state)
    evidence = client.get(f"/api/v1/sessions/{session.session_id}/evidence", headers=headers(learner))
    assert evidence.status_code == 200
    item = next(i for i in evidence.json()["items"] if i["question_id"] == future["question_id"])
    assert item["prompt"] == future["prompt"] and Decimal(item["points"]) == Decimal(future["points"])


def test_assembly_deduplicates_version_families_and_handles_shared_skills():
    q = lambda i, kind="mcq", family=None: Row(question_id=i, family_id=family, question_type=kind)
    pool = [(q(1), [1, 2]), (q(2, family=1), [1]), (q(3), [2]), (q(4, "sql"), [1])]
    result = select_questions(pool, [1, 2], {"mcq": 2, "sql": 1}, rng=Random(7))
    assert len({item.family_id or item.question_id for item in result}) == 3
    with pytest.raises(AppError, match="approved question bank"):
        select_questions(pool[:2], [1, 2], {"mcq": 2}, rng=Random(7))


@pytest.mark.parametrize("case", ["skill_coverage", "shared_family"])
def test_practice_balances_formats_without_rejecting_a_feasible_selection(case):
    from app.services.personalized_assessment import select_practice_questions

    q = lambda i, kind="mcq", family=None: Row(question_id=i, family_id=family, question_type=kind)
    if case == "skill_coverage":
        pool = [(q(1), [1]), (q(2), [2]), (q(3, "sql"), [3]), (q(4, "essay"), [3])]
        concepts, count = [1, 2, 3], 3
    else:
        pool = [(q(1), [1]), (q(2, "sql", family=1), [1]), (q(3, "essay"), [1])]
        concepts, count = [1], 2
    chosen, quotas = select_practice_questions(pool, concepts, count, rng=Random(7))
    assert len(chosen) == len({item.family_id or item.question_id for item in chosen}) == count
    assert Counter(item.question_type for item in chosen) == Counter({kind: n for kind, n in quotas.items() if n})
    assert set(concepts) <= {cid for item in chosen for q, tags in pool if item.question_id == q.question_id for cid in tags}


def test_practice_feasibility_matches_an_independent_exhaustive_small_bank_oracle():
    from app.services.personalized_assessment import select_practice_questions

    generator = Random(20261018)
    for case in range(100):
        concepts = generator.sample([1, 2, 3], generator.randint(1, 3))
        count = generator.randint(1, 4)
        pool = [(Row(question_id=i, family_id=generator.randint(1, 4),
                     question_type=generator.choice(["mcq", "sql", "essay"])),
                 generator.sample(concepts, generator.randint(1, len(concepts))))
                for i in range(1, generator.randint(1, 8) + 1)]
        feasible = any(len({q.family_id for q, _ in subset}) == count
                       and set(concepts) <= {cid for _, tags in subset for cid in tags}
                       for subset in combinations(pool, count))
        if not feasible:
            with pytest.raises(AppError) as error:
                select_practice_questions(pool, concepts, count, rng=Random(case))
            assert error.value.code == "insufficient_question_pool"
        else:
            chosen, _ = select_practice_questions(pool, concepts, count, rng=Random(case))
            assert len(chosen) == len({q.family_id for q in chosen}) == count
            assert set(concepts) <= {cid for q, tags in pool if q in chosen for cid in tags}


@pytest.mark.parametrize("policy", ["IMMEDIATE", "HUMAN_VERIFIED"])
def test_complete_real_grading_and_publication_journey(client, db_session, policy):
    admin, learner, _, _, state, _ = started(client, db_session, policy=policy)
    state = complete(client, db_session, learner, state)
    sid = state["session_id"]
    admin_headers = headers(admin, "Administrator")
    paths = ["evidence", "competency", "gaps", "guidance"]
    if policy == "HUMAN_VERIFIED":
        assert state["release_status"] == "pending_review"
        for path in paths:
            result = client.get(f"/api/v1/sessions/{sid}/{path}", headers=headers(learner))
            assert result.status_code == 409 and result.json()["error"]["code"] == "results_pending"
        history = client.get("/api/v1/sessions", headers=headers(learner)).json()[0]
        assert history["overall_result_pct"] is None and history["concepts"] == []
        assert client.get("/api/v1/sessions/competency/cumulative", headers=headers(learner)).json()["concepts"] == []
        assert client.get("/api/v1/admin/grading-reviews", headers=headers(learner)).status_code == 403
        assert client.get("/api/v1/admin/grading-reviews").status_code == 401
        review = client.get(f"/api/v1/admin/grading-reviews/{sid}", headers=admin_headers).json()
        assert client.post(f"/api/v1/admin/grading-reviews/{sid}/publish", headers=admin_headers, json={"revision": review["revision"]}).status_code == 409
        for item in review["items"]:
            if item["question_type"] not in {"sql", "essay"}:
                continue
            result = client.post(f"/api/v1/admin/grading-reviews/{sid}/attempts/{item['attempt_id']}",
                headers=admin_headers, json={"revision": item["revision"], "score": "0.50", "comments": "Verified against rubric and execution evidence"})
            assert result.status_code == 200, result.json()
            review = result.json()
        assert review["release_status"] == "reviewed"
        result = client.post(f"/api/v1/admin/grading-reviews/{sid}/publish", headers=admin_headers, json={"revision": review["revision"]})
        assert result.status_code == 200 and result.json()["release_status"] == "published"
        assert db_session.scalar(select(func.count()).select_from(GradeReview)) == 3
        for stored in db_session.scalars(select(GradeReview)):
            assert stored.automated_score == 1 and stored.approved_score == Decimal("0.50")
        assert client.get("/api/v1/admin/grading-reviews", headers=admin_headers).json() == []
    else:
        assert state["release_status"] == "published"
    for path in paths[:2]:
        assert client.get(f"/api/v1/sessions/{sid}/{path}", headers=headers(learner)).status_code == 200
    history = client.get("/api/v1/sessions", headers=headers(learner)).json()[0]
    expected = Decimal("88.46") if policy == "HUMAN_VERIFIED" else Decimal(100)
    assert Decimal(history["overall_result_pct"]) == expected
    cumulative = client.get("/api/v1/sessions/competency/cumulative", headers=headers(learner)).json()
    assert cumulative["summary"]["finalized_assessments"] == 1
    assert sum(len(c["contributing_attempts"]) for c in cumulative["concepts"]) == 13
    assert client.get(f"/api/v1/admin/learners/{learner.account_id}/competency/cumulative", headers=admin_headers).json() == cumulative


@pytest.mark.parametrize("score", ["-1", "1.01", "NaN", "Infinity", "0.001", True])
def test_invalid_review_score_rejected(client, db_session, score):
    admin, learner, _, _, state, _ = started(client, db_session, policy="HUMAN_VERIFIED", skills=1)
    # A manually finalized fixture retains real snapshot bounds for validation.
    sid = state["session_id"]
    attempt = db_session.get(Attempt, state["current_question"]["attempt_id"])
    session = db_session.get(AssessmentSession, sid)
    attempt.score = Decimal(1)
    attempt.submitted_at = session.started_at
    attempt.grading_status = "graded"
    session.status = "completed"
    session.release_status = "pending_review"
    db_session.commit()
    result = client.post(f"/api/v1/admin/grading-reviews/{sid}/attempts/{attempt.attempt_id}", headers=headers(admin, "Administrator"), json={"revision": 0, "score": score})
    assert result.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(GradeReview)) == 0


def test_review_conflict_audit_immutability_and_ownership(client, db_session):
    admin, learner, _, _, state, _ = started(client, db_session, policy="HUMAN_VERIFIED", skills=1)
    sid = state["session_id"]
    session = db_session.get(AssessmentSession, sid)
    attempt = db_session.get(Attempt, state["current_question"]["attempt_id"])
    session.status = "completed"
    session.release_status = "pending_review"
    attempt.submitted_at = session.started_at
    attempt.grading_status = "graded"
    attempt.score = Decimal(1)
    db_session.commit()
    def approve(_):
        with TestClient(app) as api:
            return api.post(f"/api/v1/admin/grading-reviews/{sid}/attempts/{attempt.attempt_id}", headers=headers(admin, "Administrator"), json={"revision": 0}).status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(approve, range(2))) == [200, 409]
    assert db_session.scalar(select(func.count()).select_from(GradeReview)) == 1
    with pytest.raises(Exception):
        with db_session.begin_nested():
            db_session.execute(text("UPDATE grade_review SET approved_score=0"))
    other = _make_account(db_session, "other-supervisor@test.dev", "Learner")
    for suffix in ("", "/evidence", "/competency", "/gaps", "/guidance"):
        assert client.get(f"/api/v1/sessions/{sid}{suffix}", headers=headers(other)).status_code == 404


def test_concept_metadata_roundtrip_validation_and_existing_fields(client, db_session):
    admin = _make_account(db_session, "metadata-admin@test.dev", "Administrator")
    h = headers(admin, "Administrator")
    payload = {"concept_code": "META", "concept_name": "Metadata", "subject_area": "SQL",
               "description": "Existing description", "keywords": [" JOIN ", "JOIN", ""],
               "learning_objectives": ["Explain join semantics"]}
    result = client.post("/api/v1/admin/concepts", headers=h, json=payload)
    assert result.status_code == 201
    assert result.json()["keywords"] == ["JOIN"]
    cid = result.json()["concept_id"]
    patch = client.patch(f"/api/v1/admin/concepts/{cid}", headers=h, json={"learning_objectives": ["Compare outer joins"]})
    assert patch.json()["description"] == payload["description"] and patch.json()["keywords"] == ["JOIN"]
    assert patch.json()["learning_objectives"] == ["Compare outer joins"]
    assert client.patch(f"/api/v1/admin/concepts/{cid}", headers=h, json={"keywords": ["x" * 101]}).status_code == 422
    assert client.patch(f"/api/v1/admin/concepts/{cid}", headers=h, json={"keywords": ["x\u0000y"]}).status_code == 422


def test_cumulative_pooling_is_weighted_published_and_uses_historical_context():
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    c = {"concept_id": 1, "concept_code": "C", "concept_name": "Original", "subject_area": "SQL", "description": None}
    def session(sid, status="published"):
        return Row(session_id=sid, status="completed", release_status=status, started_at=now,
                   config_snapshot={"concepts": [{**c, "target_pct": "70"}]})
    def attempt(aid, earned, possible, submitted=True):
        return Row(attempt_id=aid, submitted_at=now if submitted else None, score=Decimal(earned) if earned is not None else None,
            grading_status="graded" if earned is not None and submitted else "pending",
            question_snapshot={"question_id": aid, "question_type": "mcq", "points": possible, "concepts": [c]}, question=None)
    sessions = [session(1), session(2), session(3, "pending_review")]
    attempts = {1: [attempt(1, "1", "1")], 2: [attempt(2, "0", "9"), attempt(4, None, "100"), attempt(5, "0", "100", False)], 3: [attempt(3, "99", "99")]}
    result = aggregate_sessions(sessions, attempts, {1: {1: Decimal(60)}, 2: {1: Decimal(80)}, 3: {1: Decimal(70)}})[1]
    assert result["earned"] == 1 and result["possible"] == 10  # 10%, never the 50% average of two assessments
    assert result["target_weight"] / result["target_possible"] == 78
    assert result["session_ids"] == [1, 2] and result["attempt_ids"] == [1, 2]
    assert result["below_count"] == result["meeting_count"] == 1
    assert result["concept"].concept_name == "Original"


def test_empty_cumulative_profile_is_private_and_provider_independent(client, db_session):
    learner = _make_account(db_session, "empty-profile@test.dev", "Learner")
    result = client.get("/api/v1/sessions/competency/cumulative", headers=headers(learner))
    assert result.status_code == 200 and result.json()["concepts"] == []
    assert result.json()["summary"]["finalized_assessments"] == 0
    assert client.get("/api/v1/sessions/competency/cumulative").status_code == 401


def pending_manual_case(db, policy="HUMAN_VERIFIED"):
    from app.services.evidence_context import capture_assessment, capture_question
    learner, original, _, question, _, _, _ = _fixture(db, "essay")
    repo = AssessmentRepository(db)
    session = repo.create_session(original.assessment_id, learner.account_id, original.expires_at,
                                  result_release_policy=policy)
    snapshot = capture_assessment(original.assessment)
    snapshot["result_release_policy"] = policy
    session.config_snapshot = snapshot
    session.status = "completed"
    session.release_status = "auto_grading"
    session.submitted_at = repo.server_time()
    attempt = repo.create_attempt(session.session_id, question.question_id, 1)
    attempt.question_snapshot = capture_question(repo, question)
    attempt.essay_answer = "3NF"
    attempt.submitted_at = session.submitted_at
    attempt.grading_detail = {"grader": "pending", "error_code": "llm_not_configured"}
    repo.enqueue_grading(attempt)
    admin = _make_account(db, "manual-grader@test.dev", "Administrator")
    db.commit()
    return admin, learner, session, attempt


@pytest.mark.parametrize("grading_status", ["pending", "failed"])
def test_manual_takeover_requires_reason_and_preserves_unavailable_automation(client, db_session, grading_status):
    admin, learner, session, attempt = pending_manual_case(db_session)
    attempt.grading_status = grading_status
    db_session.commit()
    path = f"/api/v1/admin/grading-reviews/{session.session_id}/attempts/{attempt.attempt_id}"
    h = headers(admin, "Administrator")
    assert client.post(path, headers=h, json={"revision": 0, "score": "0.5"}).status_code == 422
    result = client.post(path, headers=h, json={"revision": 0, "score": "0.5", "comments": "Manually evaluated the rubric while the provider was unavailable"})
    assert result.status_code == 200 and result.json()["release_status"] == "reviewed"
    review = db_session.scalar(select(GradeReview).where(GradeReview.attempt_id == attempt.attempt_id))
    assert review.automated_score is None and review.automated_detail["error_code"] == "llm_not_configured"
    assert db_session.scalar(select(GradingJob).where(GradingJob.attempt_id == attempt.attempt_id)).status == "completed"
    assert client.get(f"/api/v1/sessions/{session.session_id}/competency", headers=headers(learner)).status_code == 409
    published = client.post(f"/api/v1/admin/grading-reviews/{session.session_id}/publish", headers=h, json={"revision": result.json()["revision"]})
    assert published.status_code == 200
    profile = client.get(f"/api/v1/sessions/{session.session_id}/competency", headers=headers(learner)).json()
    assert profile["concepts"][0]["competency_pct"] == "50.00"


def test_manual_takeover_invalidates_a_running_grading_lease(client, db_session, monkeypatch):
    import threading
    from app.services import grading_jobs
    admin, _, session, attempt = pending_manual_case(db_session)
    started, release = threading.Event(), threading.Event()
    def delayed_grade(*args):
        started.set()
        assert release.wait(15)
        return {"score": Decimal(1), "grading_detail": {"grader": "late_auto", "points_earned": "1"}}
    monkeypatch.setattr(grading_jobs, "grade_attempt", delayed_grade)
    def worker():
        with get_session_factory()() as db:
            return grading_jobs.process_one(db, None, None, include_essay=True)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(worker)
        try:
            assert started.wait(10)
            result = client.post(f"/api/v1/admin/grading-reviews/{session.session_id}/attempts/{attempt.attempt_id}",
                headers=headers(admin, "Administrator"), json={"revision": 0, "score": "0.25", "comments": "Manual review supersedes the stalled provider"})
            assert result.status_code == 200, result.json()
        finally:
            release.set()
        assert future.result(timeout=20)
    db_session.refresh(attempt)
    assert attempt.score == Decimal("0.25") and attempt.grading_detail["grader"] == "human_verified"


def test_self_review_and_self_publication_forbidden_even_with_both_roles(client, db_session):
    admin, learner, session, attempt = pending_manual_case(db_session)
    admin_role = db_session.scalar(select(Role).where(Role.role_name == "Administrator"))
    db_session.add(AccountRole(account_id=learner.account_id, role_id=admin_role.role_id))
    db_session.commit()
    h = headers(learner, "Administrator")
    base = f"/api/v1/admin/grading-reviews/{session.session_id}"
    assert client.post(f"{base}/attempts/{attempt.attempt_id}", headers=h, json={"revision": 0, "score": "0.5", "comments": "Own submission"}).status_code == 403
    assert client.post(f"{base}/publish", headers=h, json={"revision": 0}).status_code == 403


def test_new_sessions_default_to_unpublished_including_human_mode(db_session):
    _, learner, _, a = bank(db_session)
    for policy in ("IMMEDIATE", "HUMAN_VERIFIED"):
        session = AssessmentSession(assessment_id=a.assessment_id, learner_id=learner.account_id,
            expires_at=AssessmentRepository(db_session).server_time() + timedelta(hours=1),
            result_release_policy=policy, status="completed")
        db_session.add(session)
        db_session.flush()
        assert session.release_status == "unsubmitted"


def test_cumulative_multiple_published_attempts_use_pooled_points_and_keep_individual_history(client, db_session):
    from test_competency import _make_learner, _make_concept, _make_session, _add_question, _add_attempt
    learner = _make_learner(db_session)
    c = _make_concept(db_session, "POOLED")
    first = _make_session(db_session, learner, targets={c: 60})
    second = _make_session(db_session, learner, targets={c: 80})
    q1 = _add_question(db_session, learner.account_id, points=1, concept_ids=[c.concept_id])
    q2 = _add_question(db_session, learner.account_id, points=9, concept_ids=[c.concept_id])
    _add_attempt(db_session, first, q1, 1, score=1)
    _add_attempt(db_session, second, q2, 1, score=0)
    db_session.commit()
    result = client.get("/api/v1/sessions/competency/cumulative", headers=headers(learner)).json()
    item = result["concepts"][0]
    assert item["competency_pct"] == "10.00" and item["target_pct"] == "78.00"
    assert item["contributing_sessions"] == [first.session_id, second.session_id]
    assert item["below_target_assessments"] == 1
    history = client.get("/api/v1/sessions", headers=headers(learner)).json()
    assert {s["overall_result_pct"] for s in history} == {"100.00", "0.00"}
    assert client.get("/api/v1/sessions/competency/cumulative", headers=headers(learner)).json() == result


def test_practice_sessions_never_enter_official_competency(client, db_session):
    from test_competency import _make_learner, _make_concept, _make_session, _add_question, _add_attempt
    learner = _make_learner(db_session, email="practice-exclusion@test.dev")
    c = _make_concept(db_session, "PRACTICE-EXCLUDED")
    practice = _make_session(db_session, learner, targets={c: 60})
    practice.config_snapshot = {"assembly_mode": "PRACTICE"}
    formal = _make_session(db_session, learner, targets={c: 80})
    formal.config_snapshot = {"assembly_mode": "FORMAL"}
    legacy = _make_session(db_session, learner, targets={c: 60})
    q = _add_question(db_session, learner.account_id, points=1, concept_ids=[c.concept_id])
    _add_attempt(db_session, practice, q, 1, score=0)
    _add_attempt(db_session, formal, q, 1, score=1)
    _add_attempt(db_session, legacy, q, 1, score=1)
    db_session.commit()
    result = client.get("/api/v1/sessions/competency/cumulative", headers=headers(learner)).json()
    assert result["summary"]["finalized_assessments"] == 2
    assert practice.session_id not in result["concepts"][0]["contributing_sessions"]
    assert set(result["concepts"][0]["contributing_sessions"]) == {formal.session_id, legacy.session_id}
    assert result["concepts"][0]["competency_pct"] == "100.00"


def test_immediate_incomplete_grading_never_exposes_official_partial_results(client, db_session):
    from app.services.grading_jobs import process_one
    _, learner, session, _ = pending_manual_case(db_session, "IMMEDIATE")
    h = headers(learner)
    for endpoint in ("evidence", "competency", "gaps", "guidance"):
        assert client.get(f"/api/v1/sessions/{session.session_id}/{endpoint}", headers=h).status_code == 409
    history = client.get("/api/v1/sessions", headers=h).json()
    item = next(s for s in history if s["session_id"] == session.session_id)
    assert item["overall_result_pct"] is None and item["concepts"] == []
    settings = get_settings().model_copy(update={"grading_job_max_attempts": 1})
    assert process_one(db_session, None, None, include_essay=True, settings=settings)
    assert client.get(f"/api/v1/sessions/{session.session_id}", headers=h).json()["release_status"] == "grading_failed"
    assert client.get("/api/v1/sessions/competency/cumulative", headers=h).json()["concepts"] == []


def test_invalid_ai_output_in_human_mode_saves_answer_for_verification_without_a_score(client, db_session):
    from app.models import LlmCache
    from app.services.evidence_context import capture_assessment, capture_question
    from test_llm_release import _service, _grade_payload
    learner, original, _, question, _, _, _ = _fixture(db_session, "essay")
    repo = AssessmentRepository(db_session)
    session = repo.create_session(original.assessment_id, learner.account_id, original.expires_at,
                                  result_release_policy="HUMAN_VERIFIED")
    snapshot = capture_assessment(original.assessment)
    snapshot["result_release_policy"] = "HUMAN_VERIFIED"
    session.config_snapshot = snapshot
    attempt = repo.create_attempt(session.session_id, question.question_id, 1)
    attempt.question_snapshot = capture_question(repo, question)
    db_session.commit()
    service = _service(db_session, _grade_payload(score=999))
    app.dependency_overrides[get_llm_service] = lambda: service
    try:
        result = client.post(f"/api/v1/sessions/{session.session_id}/answers", headers=headers(learner),
            json={"question_id": question.question_id, "essay_answer": "3NF definition"})
        assert result.status_code == 200, result.json()
        assert result.json()["score"] is None and result.json()["is_correct"] is None
        assert result.json()["grading_status"] == "pending"
        db_session.refresh(attempt)
        assert attempt.essay_answer == "3NF definition" and attempt.score is None
        assert db_session.scalar(select(func.count()).select_from(LlmCache)) == 0
    finally:
        app.dependency_overrides.pop(get_llm_service, None)


@pytest.mark.parametrize("count", [1, 2, 3, 5])
def test_explicit_topic_practice_uses_requested_length_and_existing_grading(client, db_session, count):
    _, learner, concepts, a = bank(db_session, skills=1, difficulty=3)
    request = {**selection(concepts, "MEDIUM"), "mode": "PRACTICE", "question_count": count}
    response = client.post(f"/api/v1/assessments/{a.assessment_id}/sessions", headers=headers(learner), json=request)
    assert response.status_code == 201, response.json()
    state = response.json()
    assert state["max_questions"] == count and state["assembly_mode"] == "PRACTICE"
    snapshot = db_session.get(AssessmentSession, state["session_id"]).config_snapshot
    assert len(snapshot["question_plan"]) == count
    assert snapshot["template_limits"]["max_questions"] == 13
    assert {q["difficulty_level"] for q in snapshot["question_plan"]} == {3}
    final = complete(client, db_session, learner, state)
    assert final["release_status"] == "published"
    profile = client.get(f"/api/v1/sessions/{state['session_id']}/competency", headers=headers(learner)).json()
    assert Decimal(profile["concepts"][0]["points_possible"]) == Decimal(count)
    assert profile["concepts"][0]["competency_pct"] == "100.00"


def test_conceptual_practice_does_not_require_unrelated_sql_questions(client, db_session):
    admin = _make_account(db_session, "conceptual-admin@test.dev", "Administrator")
    learner = _make_account(db_session, "conceptual-learner@test.dev", "Learner")
    concept = _concept(db_session, "DESIGN-PRACTICE")
    _mcq(db_session, concept, diff=3, admin=admin)
    _mcq(db_session, concept, diff=3, admin=admin)
    _essay(db_session, concept, diff=3, admin=admin)
    a = _assessment(db_session, admin, [concept], complete=False)
    db_session.commit()
    request = {**selection([concept], "MEDIUM"), "mode": "PRACTICE", "question_count": 3}
    response = client.post(f"/api/v1/assessments/{a.assessment_id}/sessions", headers=headers(learner), json=request)
    assert response.status_code == 201
    config = db_session.get(AssessmentSession, response.json()["session_id"]).config_snapshot
    assert Counter(q["question_type"] for q in config["question_plan"]) == {"mcq": 2, "essay": 1}
    assert config["target_sql"] == 0
    final = complete(client, db_session, learner, response.json())
    assert final["answered_count"] == 3


@pytest.mark.parametrize("extra", [{"mode": "FORMAL", "question_count": 3}, {"mode": "PRACTICE", "question_count": True}, {"mode": "PRACTICE", "question_count": 4}])
def test_short_count_requires_explicit_practice_and_valid_integer(client, db_session, extra):
    _, learner, concepts, a = bank(db_session)
    result = client.post(f"/api/v1/assessments/{a.assessment_id}/sessions", headers=headers(learner), json={**selection(concepts), **extra})
    assert result.status_code == 422


def test_practice_request_id_cannot_change_mode_or_length(client, db_session):
    _, learner, concepts, a = bank(db_session, skills=1)
    payload = {**selection(concepts), "mode": "PRACTICE", "question_count": 3}
    path = f"/api/v1/assessments/{a.assessment_id}/sessions"
    first = client.post(path, headers=headers(learner), json=payload)
    assert first.status_code == 201
    assert client.post(path, headers=headers(learner), json=payload).json()["session_id"] == first.json()["session_id"]
    for extra in ({"question_count": 5}, {"mode": "FORMAL", "question_count": 13}):
        result = client.post(path, headers=headers(learner), json={**payload, **extra})
        assert result.status_code == 409 and result.json()["error"]["code"] == "start_request_conflict"


def test_type_quota_deduplication_handles_families_with_different_version_types():
    pool = [(Row(question_id=1, family_id=None, question_type="mcq"), [1]),
            (Row(question_id=2, family_id=1, question_type="sql"), [1])]
    with pytest.raises(AppError):
        select_questions(pool, [1], {"mcq": 1, "sql": 1})


def test_insufficient_skill_coverage_does_not_search_equivalent_question_permutations():
    pool = []
    for cid in range(1, 13):
        for version in range(4):
            pool.append((Row(question_id=cid * 10 + version, family_id=None, question_type="mcq"), [cid]))
    for qid, kind in ((200, "sql"), (201, "sql"), (202, "essay")):
        pool.append((Row(question_id=qid, family_id=None, question_type=kind), [1]))
    with pytest.raises(AppError):
        select_questions(pool, list(range(1, 13)), {"mcq": 10, "sql": 2, "essay": 1})


def test_admin_can_requeue_terminal_grading_failure_without_a_provider_call(client, db_session):
    from app.services.grading_jobs import process_one
    admin, learner, session, attempt = pending_manual_case(db_session, "IMMEDIATE")
    settings = get_settings().model_copy(update={"grading_job_max_attempts": 1})
    assert process_one(db_session, None, None, include_essay=True, settings=settings)
    queue = client.get("/api/v1/admin/grading-reviews", headers=headers(admin, "Administrator")).json()
    assert any(s["session_id"] == session.session_id and s["release_status"] == "grading_failed" for s in queue)
    detail = client.get(f"/api/v1/admin/grading-reviews/{session.session_id}", headers=headers(admin, "Administrator")).json()
    path = f"/api/v1/admin/grading-reviews/{session.session_id}/retry"
    assert client.post(path, headers=headers(learner), json={"revision": detail["revision"]}).status_code == 403
    result = client.post(path, headers=headers(admin, "Administrator"), json={"revision": detail["revision"]})
    assert result.status_code == 200 and result.json()["release_status"] == "auto_grading"
    db_session.refresh(attempt)
    assert attempt.score is None and attempt.grading_status == "pending"
    job = db_session.scalar(select(GradingJob).where(GradingJob.attempt_id == attempt.attempt_id))
    assert job.status == "pending" and job.attempt_count == 0
    assert client.post(path, headers=headers(admin, "Administrator"), json={"revision": detail["revision"]}).status_code == 409
    assert process_one(db_session, None, _essay_service(db_session), include_essay=True)
    result = client.get(f"/api/v1/sessions/{session.session_id}/competency", headers=headers(learner))
    assert result.status_code == 200 and result.json()["concepts"][0]["competency_pct"] == "100.00"


def test_reserved_future_questions_block_deletion_and_clone_edits_with_original_option_ids(client, db_session):
    from app.models import McqOption, SessionQuestionPlan
    admin, learner, _, _, state, _ = started(client, db_session)
    sid = state["session_id"]
    config = db_session.get(AssessmentSession, sid).config_snapshot
    future = next(q for q in config["question_plan"][1:] if q["question_type"] == "mcq")
    qid = future["question_id"]
    assert db_session.scalar(select(func.count()).select_from(SessionQuestionPlan).where(SessionQuestionPlan.session_id == sid)) == 13
    h = headers(admin, "Administrator")
    assert client.delete(f"/api/v1/admin/questions/{qid}", headers=h).status_code == 409
    payload = {"question_type": "mcq", "prompt": "Edited bank content for future assessments", "points": "2",
        "difficulty_level": 4, "concept_ids": [c["concept_id"] for c in future["concepts"]],
        "options": [{"option_label": "A", "option_text": "Changed A", "is_correct": True},
                    {"option_label": "B", "option_text": "Changed B", "is_correct": False}]}
    edited = client.put(f"/api/v1/admin/questions/{qid}", headers=h, json=payload)
    assert edited.status_code == 200, edited.json()
    assert edited.json()["question_id"] != qid
    db_session.expire_all()
    assert {o["option_id"] for o in future["options"]} <= set(db_session.scalars(select(McqOption.option_id).where(McqOption.question_id == qid)))
    with pytest.raises(Exception):
        with db_session.begin_nested():
            db_session.execute(text("UPDATE session_question_plan SET seq_no=seq_no WHERE session_id=:sid"), {"sid": sid})
    final = complete(client, db_session, learner, state)
    assert final["release_status"] == "published"
    history = client.get("/api/v1/sessions", headers=headers(learner)).json()[0]
    assert history["overall_result_pct"] == "100.00"


def test_retried_job_does_not_reuse_a_stale_workers_generation(client, db_session, monkeypatch):
    import threading
    from app.services import grading_jobs, grading_review
    admin, _, session, attempt = pending_manual_case(db_session, "IMMEDIATE")
    waiting, release = threading.Event(), threading.Event()
    def old_grade(*args):
        waiting.set()
        assert release.wait(15)
        return {"score": Decimal(1), "grading_detail": {"grader": "expired_worker"}}
    monkeypatch.setattr(grading_jobs, "grade_attempt", old_grade)
    def old_worker():
        with get_session_factory()() as db:
            return grading_jobs.process_one(db, None, None, include_essay=True)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(old_worker)
        try:
            assert waiting.wait(10)
            # Model a recovered lease reaching its retry limit while the old
            # transport is still running, followed by an authorized retry.
            repo = AssessmentRepository(db_session)
            session = repo.lock_session(session.session_id)
            attempt.grading_status = "failed"
            job = db_session.scalar(select(GradingJob).where(GradingJob.attempt_id == attempt.attempt_id))
            job.status, job.attempt_count, job.lease_until = "failed", 3, None
            db_session.flush()
            grading_review.reconcile(db_session, session)
            db_session.commit()
            result = client.post(f"/api/v1/admin/grading-reviews/{session.session_id}/retry",
                headers=headers(admin, "Administrator"), json={"revision": session.review_revision})
            assert result.status_code == 200, result.json()
            with get_session_factory()() as fresh:
                next_claim = AssessmentRepository(fresh).claim_grading_job(include_essay=True)
                assert next_claim.attempt_count == 1
                next_deadline = next_claim.lease_until
                fresh.commit()
        finally:
            release.set()
        assert future.result(timeout=20)
    db_session.refresh(attempt)
    db_session.refresh(job)
    assert attempt.score is None and attempt.grading_status == "pending"
    assert job.status == "processing" and job.lease_until == next_deadline


def test_competency_storage_accepts_the_full_valid_question_points_range(client, db_session):
    from test_competency import _make_learner, _make_concept, _make_session, _add_question, _add_attempt
    learner = _make_learner(db_session)
    concept = _make_concept(db_session, "MAX-POINTS")
    session = _make_session(db_session, learner, targets={concept: 60})
    for seq in range(1, 14):
        question = _add_question(db_session, learner.account_id, points="999.99", concept_ids=[concept.concept_id])
        _add_attempt(db_session, session, question, seq, score="999.99")
    db_session.commit()
    result = client.get(f"/api/v1/sessions/{session.session_id}/competency", headers=headers(learner))
    assert result.status_code == 200, result.json()
    item = result.json()["concepts"][0]
    assert item["points_earned"] == item["points_possible"] == "12999.87"
    assert item["competency_pct"] == "100.00"
    cumulative = client.get("/api/v1/sessions/competency/cumulative", headers=headers(learner)).json()
    assert cumulative["concepts"][0]["points_possible"] == "12999.87"
