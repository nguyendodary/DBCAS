"""Server-owned session purpose and cumulative-competency separation."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from app.models import AssessmentSession, Attempt, CloConcept, CourseLearningOutcome
from app.repositories import AssessmentRepository
from test_adaptive_engine import _concept, _make_account
from test_competency import (
    _add_attempt,
    _add_question,
    _make_concept,
    _make_learner,
    _make_session,
)
from test_learner_practice import _fixed_payload, fixture as fixed_fixture
from test_supervisor_requirements import bank, headers


def test_create_session_defaults_to_fail_closed_practice(client, db_session):
    admin = _make_account(db_session, "purpose-admin@test.dev", "Administrator")
    learner = _make_account(db_session, "purpose-learner@test.dev", "Learner")
    concept = _concept(db_session, "PURPOSE-DEFAULT")

    from test_adaptive_engine import _assessment
    assessment = _assessment(db_session, admin, [concept], complete=False)
    session = AssessmentRepository(db_session).create_session(
        assessment.assessment_id, learner.account_id, datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db_session.commit()

    assert session.purpose == "PRACTICE"
    assert session.purpose_source == "SERVER"
    history = client.get("/api/v1/sessions", headers=headers(learner)).json()
    assert history[0]["purpose"] == "PRACTICE"


def test_legacy_assessment_start_without_body_is_test(client, db_session):
    _, learner, _, assessment = bank(db_session, skills=1)
    response = client.post(
        f"/api/v1/assessments/{assessment.assessment_id}/sessions",
        headers=headers(learner),
    )
    assert response.status_code == 201, response.json()
    state = response.json()
    assert state["purpose"] == "TEST"

    session = db_session.get(AssessmentSession, state["session_id"])
    assert (session.purpose, session.purpose_source) == ("TEST", "SERVER")
    history = client.get("/api/v1/sessions", headers=headers(learner)).json()
    assert history[0]["purpose"] == "TEST"
    assert client.get(f"/api/v1/sessions/{state['session_id']}",
                      headers=headers(learner)).json()["purpose"] == "TEST"


def test_cumulative_separates_official_practice_backfill_provisional_and_adaptive(
    client, db_session
):
    learner = _make_learner(db_session, email="purpose-cumulative@test.dev")
    concept = _make_concept(db_session, "PURPOSE-CUMULATIVE")
    question = _add_question(
        db_session, learner.account_id, points=1, concept_ids=[concept.concept_id]
    )

    official = _make_session(db_session, learner, targets={concept: 60})
    _add_attempt(db_session, official, question, 1, score=1)

    practice = _make_session(db_session, learner, targets={concept: 60}, purpose="PRACTICE")
    _add_attempt(db_session, practice, question, 1, score=1)

    backfill = _make_session(db_session, learner, targets={concept: 60})
    backfill.purpose_source = "BACKFILL"
    _add_attempt(db_session, backfill, question, 1, score=1)

    provisional = _make_session(db_session, learner, targets={concept: 60})
    provisional.release_status = "provisional_ai"
    _add_attempt(db_session, provisional, question, 1, score=1)

    pending = _make_session(db_session, learner, targets={concept: 60})
    pending.release_status = "pending_review"
    _add_attempt(db_session, pending, question, 1, score=1)

    formal_adaptive = _make_session(db_session, learner, targets={concept: 60}, purpose="TEST")
    formal_adaptive.config_snapshot = {"version": 1, "assembly_mode": "ADAPTIVE"}
    _add_attempt(db_session, formal_adaptive, question, 1, score=1)

    adaptive = _make_session(db_session, learner, purpose="TEST")
    adaptive.config_snapshot = {
        "version": 1,
        "title": "Adaptive practice",
        "assembly_mode": "PRACTICE",
        "runner_mode": "adaptive",
        "result_kind": "estimated_ability",
        "adaptive": {"policy_version": "continuous-mcq-v1", "start_band": "MEDIUM"},
    }
    now = datetime.now(timezone.utc)
    for seq in range(1, 4):
        attempt = Attempt(
            session_id=adaptive.session_id,
            question_id=question.question_id,
            seq_no=seq,
            selected_option_id=None,
            submitted_at=now,
            grading_status="graded",
            grading_detail={"grader": "answer_key"},
        )
        attempt.question_snapshot = {
            "question_id": question.question_id,
            "question_type": "mcq",
            "difficulty_level": 3,
            "options": [{"option_id": 1, "is_correct": True}],
        }
        db_session.add(attempt)
    db_session.commit()

    result = client.get("/api/v1/sessions/competency/cumulative",
                        headers=headers(learner)).json()
    assert result["summary"]["finalized_assessments"] == 1
    assert result["concepts"][0]["contributing_sessions"] == [official.session_id]
    assert [item["session_id"] for item in result["adaptive_estimates"]] == [
        adaptive.session_id
    ]
    estimate = result["adaptive_estimates"][0]
    assert estimate["assessment_title"] == "Adaptive practice"
    assert estimate["band"] in {"EASY", "MEDIUM", "HARD"}
    assert estimate["evidence_count"] == 3
    assert formal_adaptive.session_id not in {
        item["session_id"] for item in result["adaptive_estimates"]
    }


def test_published_fixed_test_maps_cumulative_concepts_and_formal_statistics(
    client, db_session
):
    """A published TEST/FIXED run maps its evidenced concepts into both views."""
    admin, learner, concepts = fixed_fixture(db_session)
    clo = CourseLearningOutcome(
        clo_code="CLO-PURPOSE", title="Purpose evidence", created_by=admin.account_id
    )
    db_session.add(clo)
    db_session.flush()
    db_session.add_all([
        CloConcept(clo_id=clo.clo_id, concept_id=concept.concept_id, status="confirmed")
        for concept in concepts
    ])
    db_session.commit()

    response = client.post(
        "/api/v1/practice/start",
        headers=headers(learner),
        json=_fixed_payload(concepts),
    )
    assert response.status_code == 200, response.text
    sid = response.json()["session_id"]
    session = db_session.get(AssessmentSession, sid)
    assert session.purpose == "TEST" and session.purpose_source == "SERVER"
    assert session.config_snapshot["assessment_style"] == "FIXED"
    assert session.config_snapshot["runner_mode"] == "fixed"

    attempts = list(db_session.scalars(
        select(Attempt).where(Attempt.session_id == sid).order_by(Attempt.seq_no)
    ))
    for attempt in attempts:
        snapshot = attempt.question_snapshot
        if snapshot["question_type"] == "mcq":
            answer = {
                "selected_option_id": next(
                    option["option_id"] for option in snapshot["options"]
                    if option["is_correct"]
                )
            }
        elif snapshot["question_type"] == "sql":
            answer = {"sql_answer": snapshot["reference_answer"]}
        else:
            answer = {"essay_answer": snapshot["reference_answer"]}
        saved = client.put(
            f"/api/v1/sessions/{sid}/paper/{attempt.seq_no}/draft",
            headers=headers(learner),
            json={"revision": 1, **answer},
        )
        assert saved.status_code == 200, saved.text
    submitted = client.post(
        f"/api/v1/sessions/{sid}/paper/submit", headers=headers(learner), json={}
    )
    assert submitted.status_code == 200, submitted.text

    db_session.expire_all()
    session = db_session.get(AssessmentSession, sid)
    now = datetime.now(timezone.utc)
    for attempt in db_session.scalars(select(Attempt).where(Attempt.session_id == sid)):
        attempt.submitted_at = now
        attempt.score = Decimal(str(attempt.question_snapshot["points"]))
        attempt.grading_status = "graded"
        attempt.grading_detail = {"grader": "answer_key"}
    session.status = "completed"
    session.release_status = "published"
    session.submitted_at = now
    db_session.commit()

    evidenced = sorted({
        concept["concept_id"]
        for attempt in db_session.scalars(
            select(Attempt).where(Attempt.session_id == sid)
        )
        for concept in attempt.question_snapshot["concepts"]
    })
    profile = client.get(
        "/api/v1/sessions/competency/cumulative", headers=headers(learner)
    ).json()
    assert sorted(item["concept_id"] for item in profile["concepts"]) == evidenced
    assert profile["summary"]["finalized_assessments"] == 1
    assert profile["concepts"][0]["contributing_sessions"] == [sid]

    statistics = client.get(
        "/api/v1/admin/analytics/statistics",
        headers=headers(admin, "Administrator"),
    ).json()
    assert statistics["published_formal_sessions"] >= 1
    clo_rows = statistics["dimensions"]["clos"]
    assert any(row["label"].startswith("CLO-PURPOSE") for row in clo_rows)
    assert statistics["dimensions"]["clo_mapping_unknown_attempts"] == 0
    assert any(
        row["learner_id"] == learner.account_id for row in statistics["ranking"]
    )


def test_backfill_rows_remain_visible_in_history_but_not_cumulative(client, db_session):
    learner = _make_learner(db_session, email="purpose-history@test.dev")
    concept = _make_concept(db_session, "PURPOSE-HISTORY")
    question = _add_question(
        db_session, learner.account_id, points=1, concept_ids=[concept.concept_id]
    )
    session = _make_session(db_session, learner, targets={concept: 60})
    session.purpose_source = "BACKFILL"
    _add_attempt(db_session, session, question, 1, score=1)
    db_session.commit()

    history = client.get("/api/v1/sessions", headers=headers(learner)).json()
    assert history[0]["session_id"] == session.session_id
    assert history[0]["purpose"] == "TEST"
    assert client.get("/api/v1/sessions/competency/cumulative",
                      headers=headers(learner)).json()["concepts"] == []
