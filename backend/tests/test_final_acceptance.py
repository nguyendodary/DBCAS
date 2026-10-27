"""Independent acceptance regressions; all database fixtures are disposable."""
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.cumulative_competency import aggregate_sessions


@pytest.mark.parametrize("invalid_status", ["failed", "pending", "unsubmitted"])
def test_cumulative_excludes_nonfinal_grades_even_when_a_legacy_score_is_present(invalid_status):
    now = datetime.now(timezone.utc)
    concept = dict(concept_id=1, concept_code="SQL", concept_name="SQL", subject_area="SQL")
    session = SimpleNamespace(session_id=1, started_at=now, status="completed",
                              release_status="published", config_snapshot={"concepts": []})

    def evidence(aid, status):
        return SimpleNamespace(attempt_id=aid, score=Decimal(1), submitted_at=now,
            grading_status=status, question_snapshot={"question_id": aid,
                "question_type": "mcq", "points": "1", "concepts": [concept]})

    totals = aggregate_sessions([session], {1: [evidence(1, "graded"), evidence(2, invalid_status)]},
                                {1: {1: Decimal(70)}})[1]
    assert totals["attempt_ids"] == [1]
    assert totals["earned"] == totals["possible"] == 1


@pytest.mark.parametrize("invalid_status", ["failed", "pending", "unsubmitted"])
def test_cumulative_api_uses_only_final_grades_from_incomplete_historical_records(client, db_session, invalid_status):
    from app.repositories import AssessmentRepository
    from app.services.evidence_context import capture_assessment
    from test_adaptive_engine import _make_account, _concept, _assessment
    from test_competency import _add_question, _add_attempt
    from test_supervisor_requirements import headers

    admin = _make_account(db_session, "audit-admin@test.dev", "Administrator")
    learner = _make_account(db_session, "audit-learner@test.dev", "Learner")
    concept = _concept(db_session, "AUDIT-CUMULATIVE")
    assessment = _assessment(db_session, admin, [concept], complete=False)
    session = AssessmentRepository(db_session).create_session(
        assessment.assessment_id, learner.account_id, datetime.now(timezone.utc))
    session.status, session.release_status = "completed", "published"
    session.config_snapshot = capture_assessment(assessment)
    good = _add_attempt(db_session, session,
        _add_question(db_session, admin.account_id, points="1", concept_ids=[concept.concept_id]), 1, score="1")
    bad = _add_attempt(db_session, session,
        _add_question(db_session, admin.account_id, points="9", concept_ids=[concept.concept_id]), 2, score="0")
    bad.grading_status = invalid_status
    db_session.commit()
    for path, account, role in [
        ("/api/v1/sessions/competency/cumulative", learner, "Learner"),
        (f"/api/v1/admin/learners/{learner.account_id}/competency/cumulative", admin, "Administrator"),
    ]:
        result = client.get(path, headers=headers(account, role))
        assert result.status_code == 200
        item = result.json()["concepts"][0]
        assert item["contributing_attempts"] == [good.attempt_id]
        assert Decimal(item["competency_pct"]) == 100
        assert Decimal(item["points_possible"]) == 1
        assert not item["below_target"]


@pytest.mark.parametrize("policy", ["IMMEDIATE", "HUMAN_VERIFIED"])
def test_score_presence_does_not_publish_an_unfinished_historical_grade(client, db_session, policy):
    from app.models import Attempt
    from test_supervisor_requirements import started, headers

    _, learner, _, _, state, _ = started(client, db_session, policy=policy, skills=1)
    attempt = db_session.get(Attempt, state["current_question"]["attempt_id"])
    attempt.submitted_at = datetime.now(timezone.utc)
    attempt.score = Decimal(1)
    attempt.grading_status = "unsubmitted"
    db_session.commit()
    h = headers(learner)
    result = client.post(f"/api/v1/sessions/{state['session_id']}/finish", headers=h)
    assert result.status_code == 200
    assert result.json()["release_status"] == "auto_grading"
    for suffix in ("evidence", "competency", "gaps", "guidance"):
        response = client.get(f"/api/v1/sessions/{state['session_id']}/{suffix}", headers=h)
        assert response.status_code == 409 and response.json()["error"]["code"] == "results_pending"
    history = client.get("/api/v1/sessions", headers=h).json()[0]
    assert history["overall_result_pct"] is None and history["concepts"] == []
    assert client.get("/api/v1/sessions/competency/cumulative", headers=h).json()["concepts"] == []


@pytest.mark.parametrize("authenticated", [False, True])
@pytest.mark.parametrize("method,path,payload", [
    ("GET", "/api/v1/admin/grading-reviews", None),
    ("GET", "/api/v1/admin/grading-reviews/999999", None),
    ("POST", "/api/v1/admin/grading-reviews/999999/attempts/999999", {"revision": 0, "score": "1"}),
    ("POST", "/api/v1/admin/grading-reviews/999999/publish", {"revision": 0}),
    ("POST", "/api/v1/admin/grading-reviews/999999/retry", {"revision": 0}),
    ("GET", "/api/v1/admin/learners/999999/competency/cumulative", None),
])
def test_all_review_routes_reject_anonymous_or_learner_accounts_and_forged_role_claims(
    client, db_session, authenticated, method, path, payload
):
    from test_adaptive_engine import _make_account
    from test_supervisor_requirements import headers

    learner = _make_account(db_session, "review-boundary@test.dev", "Learner")
    # Even a signed token claiming Administrator must use current database roles.
    h = headers(learner, "Administrator") if authenticated else {}
    response = client.request(method, path, headers=h, json=payload)
    assert response.status_code == (403 if authenticated else 401)


@pytest.mark.parametrize("policy", ["IMMEDIATE", "HUMAN_VERIFIED"])
def test_answer_parameters_cannot_change_scores_or_publication_policy(client, db_session, policy):
    from app.models import AssessmentSession, Attempt
    from test_supervisor_requirements import bank, selection, headers

    _, learner, concepts, assessment = bank(db_session, policy=policy, skills=1)
    h = headers(learner)
    response = client.post(f"/api/v1/assessments/{assessment.assessment_id}/sessions", headers=h,
        json={**selection(concepts), "mode": "PRACTICE", "question_count": 1})
    assert response.status_code == 201
    state = response.json()
    attempt = db_session.get(Attempt, state["current_question"]["attempt_id"])
    wrong = next(o["option_id"] for o in attempt.question_snapshot["options"] if not o["is_correct"])
    result = client.post(f"/api/v1/sessions/{state['session_id']}/submit", headers=h, json={
        "question_id": attempt.question_id, "selected_option_id": wrong,
        "score": "999.99", "grading_detail": {"grader": "human_verified"},
        "result_release_policy": "IMMEDIATE", "release_status": "published",
    })
    assert result.status_code == 200
    db_session.expire_all()
    assert db_session.get(Attempt, attempt.attempt_id).score == 0
    session = db_session.get(AssessmentSession, state["session_id"])
    assert session.result_release_policy == policy and session.release_status == "unsubmitted"
    if policy == "HUMAN_VERIFIED":
        assert result.json()["answer"]["score"] is None
    else:
        assert Decimal(result.json()["answer"]["score"]) == 0
    finalized = client.post(f"/api/v1/sessions/{session.session_id}/finish", headers=h)
    assert finalized.status_code == 200
    assert finalized.json()["release_status"] == ("reviewed" if policy == "HUMAN_VERIFIED" else "published")


def test_populated_upgrade_withholds_legacy_stale_scores_and_preserves_all_grade_evidence(tmp_path):
    import shutil
    from pathlib import Path
    from uuid import uuid4
    import psycopg
    from app.config import ROOT_DIR, get_settings
    from app.migrate import apply_migrations

    previous = tmp_path / "previous"
    previous.mkdir()
    for migration in (ROOT_DIR / "db/migrations").glob("*.sql"):
        if int(migration.name[:3]) <= 7:
            shutil.copy2(migration, previous / migration.name)
    namespace = "acceptance_upgrade_" + uuid4().hex[:12]
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            conn.execute((Path(__file__).parent / "fixtures/schema_20261011.sql").read_text(), prepare=False)
            conn.execute("INSERT INTO account(email,password_hash) VALUES ('upgrade-audit@test.dev','not-a-login-hash')")
            conn.execute("INSERT INTO assessment(title,created_by) VALUES ('Retained assessment',1)")
            conn.execute("INSERT INTO question(question_type,prompt,created_by,points) VALUES ('mcq','Retained question',1,1)")
            for _ in range(4):
                sid = conn.execute("INSERT INTO assessment_session(assessment_id,learner_id,status,expires_at) VALUES (1,1,'completed',NOW()) RETURNING session_id").fetchone()[0]
                conn.execute("INSERT INTO attempt(session_id,question_id,seq_no,score,submitted_at) VALUES (%s,1,1,1,NOW())", (sid,))
            apply_migrations(conn, previous)
            for aid, status in enumerate(["pending", "unsubmitted", "failed", "graded"], start=1):
                conn.execute("UPDATE attempt SET grading_status=%s WHERE attempt_id=%s", (status, aid))
            evidence = conn.execute("SELECT to_jsonb(a) FROM attempt a ORDER BY attempt_id").fetchall()
            apply_migrations(conn)
            assert conn.execute("SELECT release_status FROM assessment_session ORDER BY session_id").fetchall() == [
                ("auto_grading",), ("auto_grading",), ("grading_failed",), ("published",)]
            # Migration 008 adds a review revision; every original evidence value remains.
            assert conn.execute("SELECT to_jsonb(a)-'review_revision' FROM attempt a ORDER BY attempt_id").fetchall() == evidence
            events = conn.execute("SELECT previous_status,new_status FROM result_release_event ORDER BY session_id").fetchall()
            assert events == [("published", "auto_grading"), ("published", "auto_grading")]
            assert apply_migrations(conn) == []
            conn.execute((ROOT_DIR / "db/migrations/009_incomplete_grade_release_repair.sql").read_text(), prepare=False)
            assert conn.execute("SELECT previous_status,new_status FROM result_release_event ORDER BY session_id").fetchall() == events
        finally:
            conn.execute('SET search_path TO public')
            conn.execute(f'DROP SCHEMA "{namespace}" CASCADE')


def test_release_repair_busy_database_rolls_back_and_can_be_retried(tmp_path):
    import shutil
    from uuid import uuid4
    import psycopg
    from app.config import ROOT_DIR, get_settings
    from app.migrate import apply_migrations

    previous = tmp_path / "previous"
    previous.mkdir()
    for migration in (ROOT_DIR / "db/migrations").glob("*.sql"):
        if int(migration.name[:3]) <= 8:
            shutil.copy2(migration, previous / migration.name)
    namespace = "acceptance_lock_" + uuid4().hex[:12]
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            conn.execute((ROOT_DIR / "db/schema.sql").read_text(), prepare=False)
            apply_migrations(conn, previous)
            with psycopg.connect(url) as writer:
                writer.execute(f'SET search_path TO "{namespace}"')
                writer.execute("LOCK TABLE assessment_session IN ROW EXCLUSIVE MODE")
                with pytest.raises(psycopg.errors.LockNotAvailable):
                    apply_migrations(conn)
                assert conn.execute("SELECT COUNT(*) FROM schema_migration WHERE version LIKE '009_%' OR version LIKE '010_%' OR version LIKE '011_%' OR version LIKE '012_%'").fetchone()[0] == 0
                writer.rollback()
            assert apply_migrations(conn) == [
                "009_incomplete_grade_release_repair.sql",
                "010_session_start_request_bindings.sql",
                "011_secure_role_management.sql",
                "012_question_original_locale.sql",
                "013_assessment_blueprints.sql",
                "014_adaptive_events.sql",
            ]
            assert apply_migrations(conn) == []
        finally:
            conn.execute('SET search_path TO public')
            conn.execute(f'DROP SCHEMA "{namespace}" CASCADE')


@pytest.mark.parametrize("cover_all", [False, True])
def test_comprehensive_selection_can_exceed_question_count_and_checks_real_coverage(client, db_session, cover_all):
    from sqlalchemy import func, select
    from app.models import AssessmentConcept, AssessmentSession, Question, QuestionConcept
    from test_adaptive_engine import _concept
    from test_supervisor_requirements import bank, headers, selection

    _, learner, concepts, assessment = bank(db_session, skills=1)
    extra = [_concept(db_session, f"COMPREHENSIVE-{i}") for i in range(62)]
    concepts += extra
    db_session.add_all([AssessmentConcept(assessment_id=assessment.assessment_id,
        concept_id=c.concept_id, min_difficulty=1, max_difficulty=5, target_pct=Decimal(70)) for c in extra])
    if cover_all:
        db_session.add_all([QuestionConcept(question_id=q.question_id,
            concept_id=c.concept_id, confirmed=True, tag_source="admin")
            for q in db_session.scalars(select(Question)) for c in extra])
    db_session.commit()
    response = client.post(f"/api/v1/assessments/{assessment.assessment_id}/sessions",
        headers=headers(learner), json=selection(concepts))
    if not cover_all:
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "insufficient_question_pool"
        assert db_session.scalar(select(func.count()).select_from(AssessmentSession)) == 0
    else:
        assert response.status_code == 201, response.json()
        session = db_session.get(AssessmentSession, response.json()["session_id"])
        assert session.config_snapshot["selected_concept_ids"] == sorted(c.concept_id for c in concepts)
        assert len(session.config_snapshot["question_ids"]) == 13
        assert len(set(session.config_snapshot["question_ids"])) == 13
        covered = {c["concept_id"] for q in session.config_snapshot["question_plan"] for c in q["concepts"]}
        assert covered == set(session.config_snapshot["selected_concept_ids"])
