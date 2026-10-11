"""UC12 / FR-15 / UC18 — adaptive session engine tests.

Covers the whole lifecycle end-to-end through HTTP: start/resume,
sanitized serving, the opening-three-basic-MCQs phase, adaptive
difficulty/concept selection driven by accumulated evidence, the
configured question-mix quota pressure, selection_log auditing,
max-question and pool-exhaustion termination, finish/timeout
finalization with deterministic competency recompute, and the
per-question evidence record.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.main import app
from app.deps import get_llm_service
from app.models import (
    Account,
    AccountRole,
    Assessment,
    AssessmentConcept,
    AssessmentSession,
    Attempt,
    Concept,
    McqOption,
    Question,
    QuestionConcept,
    Role,
    Rubric,
    SelectionLog,
    SqlTestDataset,
    UserProfile,
)
from app.security import hash_password


# ----------------------------------------------------------- helpers


def _login(client, email, password="Secret123!"):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]


def _make_account(db, email, role_name):
    account = Account(
        email=email, password_hash=hash_password("Secret123!"), status="active"
    )
    account.profile = UserProfile(full_name=email)
    role = db.query(Role).filter_by(role_name=role_name).one()
    db.add(account)
    db.flush()
    db.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db.commit()
    return account


def _concept(db, code):
    c = Concept(
        concept_code=code, concept_name=code, subject_area="SQL Querying",
        difficulty_level=2,
    )
    db.add(c)
    db.flush()
    return c


def _mcq(db, concept, *, diff=1, status="validated", confirmed=True,
         admin=None, prompt="MCQ?"):
    q = Question(
        question_type="mcq", prompt=prompt, difficulty_level=diff,
        points=Decimal("1.0"), status=status,
        created_by=admin.account_id,
    )
    db.add(q)
    db.flush()
    db.add(
        McqOption(question_id=q.question_id, option_label="A",
                  option_text="correct", is_correct=True)
    )
    db.add(
        McqOption(question_id=q.question_id, option_label="B",
                  option_text="wrong", is_correct=False)
    )
    db.add(
        QuestionConcept(question_id=q.question_id, concept_id=concept.concept_id,
                        confirmed=confirmed, tag_source="admin")
    )
    db.flush()
    return q


def _sql(db, concept, *, diff=2, admin=None):
    q = Question(
        question_type="sql", prompt="Write a query.", difficulty_level=diff,
        points=Decimal("1.0"), status="validated", reference_answer="SELECT 1",
        created_by=admin.account_id,
    )
    db.add(q)
    db.flush()
    db.add(
        SqlTestDataset(
            question_id=q.question_id, dataset_name="d1",
            setup_sql="CREATE TABLE t (id int); INSERT INTO t VALUES (1);",
            expected_result={"rows": [[1]], "columns": ["id"]},
            is_edge_case=False,
        )
    )
    db.add(
        QuestionConcept(question_id=q.question_id, concept_id=concept.concept_id,
                        confirmed=True, tag_source="admin")
    )
    db.add(SqlTestDataset(question_id=q.question_id, dataset_name="empty-edge",
        setup_sql="CREATE TABLE t (id int);", expected_result={"rows": [[1]]}, is_edge_case=True))
    db.flush()
    return q


def _essay(db, concept, *, diff=3, admin=None):
    q = Question(
        question_type="essay", prompt="Explain normalization.",
        difficulty_level=diff, points=Decimal("1.0"), status="validated",
        reference_answer="...", created_by=admin.account_id,
    )
    db.add(q)
    db.flush()
    for name, low, high in (("Incomplete", "0", "0.24"),
                            ("Partial", "0.25", "0.49"),
                            ("Mostly Complete", "0.50", "0.74"),
                            ("Complete", "0.75", "1.00")):
        db.add(Rubric(question_id=q.question_id, level_name=name,
                      min_score=Decimal(low), max_score=Decimal(high),
                      criteria="Clear explanation at this level"))
    db.add(
        QuestionConcept(question_id=q.question_id, concept_id=concept.concept_id,
                        confirmed=True, tag_source="admin")
    )
    db.flush()
    return q


def _complete_bank(db, admin, concepts, min_d=1, max_d=5):
    """Complement each algorithm fixture with a valid formal 10/2/1 pool."""
    ids = {c.concept_id for c in concepts}
    pool = [q for q in db.query(Question).all() if q.status == "validated"
            and min_d <= q.difficulty_level <= max_d
            and any(t.confirmed and t.concept_id in ids for t in q.concept_tags)]
    basics = sum(q.question_type == "mcq" and q.difficulty_level <= 2 for q in pool)
    for i in range(max(0, 3 - basics)):
        _mcq(db, concepts[i % len(concepts)], diff=min_d, admin=admin, prompt=f"Opening fixture {i}")
    mcqs = sum(q.question_type == "mcq" for q in pool) + max(0, 3 - basics)
    for i in range(max(0, 10 - mcqs)):
        _mcq(db, concepts[i % len(concepts)], diff=min(max(3, min_d), max_d), admin=admin, prompt=f"Remaining fixture {i}")
    for i in range(max(0, 2 - sum(q.question_type == "sql" for q in pool))):
        _sql(db, concepts[i % len(concepts)], diff=min(max(2, min_d), max_d), admin=admin)
    if not any(q.question_type == "essay" for q in pool):
        _essay(db, concepts[0], diff=min(max(3, min_d), max_d), admin=admin)
    db.flush()


def _assessment(db, admin, concepts, *, status="active", max_q=13,
                mcq=10, sql=2, essay=1, min_d=1, max_d=5, complete=True):
    if complete and min_d <= 2 and any(q.status == "validated"
            and min_d <= q.difficulty_level <= max_d
            and any(t.confirmed for t in q.concept_tags) for q in db.query(Question).all()):
        _complete_bank(db, admin, concepts, min_d, max_d)
    a = Assessment(
        title="Adaptive Midterm", status=status, created_by=admin.account_id,
        max_questions=max_q, duration_min=60,
        target_mcq=mcq, target_sql=sql, target_essay=essay,
    )
    db.add(a)
    db.flush()
    for c in concepts:
        db.add(
            AssessmentConcept(
                assessment_id=a.assessment_id, concept_id=c.concept_id,
                min_difficulty=min_d, max_difficulty=max_d,
                target_pct=Decimal("60.00"),
            )
        )
    db.flush()
    return a


def _correct_option(db, qid):
    return db.query(McqOption).filter_by(
        question_id=qid, is_correct=True
    ).one().option_id


def _answer_current(client, token, state, db, correct=True):
    q = state["current_question"]
    payload = {"question_id": q["question_id"]}
    if q["question_type"] == "mcq":
        opt = (
            _correct_option(db, q["question_id"]) if correct
            else db.query(McqOption).filter_by(
                question_id=q["question_id"], is_correct=False
            ).one().option_id
        )
        payload["selected_option_id"] = opt
    elif q["question_type"] == "sql":
        payload["sql_answer"] = "SELECT 1"
    else:
        payload["essay_answer"] = "Normalization removes redundancy."
    r = client.post(
        f"/api/v1/sessions/{state['session_id']}/answers",
        headers={"Authorization": f"Bearer {token}"}, json=payload,
    )
    assert r.status_code == 200, r.json()
    return r.json()


def _serve(client, token, session_id):
    return client.post(
        f"/api/v1/sessions/{session_id}/serve-next",
        headers={"Authorization": f"Bearer {token}"},
    )


def _logs(db, session_id):
    return (
        db.query(SelectionLog)
        .filter_by(session_id=session_id)
        .order_by(SelectionLog.seq_no)
        .all()
    )


# --------------------------------------------------------------- tests


class TestStartAndResume:
    def test_start_serves_sanitized_basic_mcq(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        learner = _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        _mcq(db_session, c, diff=1, admin=admin)
        a = _assessment(db_session, admin, [c])
        db_session.commit()

        token = _login(client, "l@test.dev")
        r = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201, r.json()
        s = r.json()
        assert s["status"] == "in_progress"
        assert s["served_count"] == 1 and s["answered_count"] == 0
        assert s["max_questions"] == 13
        q = s["current_question"]
        assert q["question_type"] == "mcq" and q["difficulty_level"] <= 2
        assert q["seq_no"] == 1
        # answer key never leaves the server
        assert "is_correct" not in q["options"][0]
        assert len(q["options"]) == 2
        # one selection_log row audited the serve
        assert len(_logs(db_session, s["session_id"])) == 1

    def test_start_resumes_live_session(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        _mcq(db_session, c, admin=admin)
        a = _assessment(db_session, admin, [c])
        db_session.commit()
        token = _login(client, "l@test.dev")
        h = {"Authorization": f"Bearer {token}"}

        first = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        ).json()
        second = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        ).json()
        assert second["session_id"] == first["session_id"]
        assert second["served_count"] == 1
        assert second["current_question"]["seq_no"] == 1

    def test_start_requires_active_assessment(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        _mcq(db_session, c, admin=admin)
        draft = _assessment(db_session, admin, [c], status="draft")
        closed = _assessment(db_session, admin, [c], status="closed")
        db_session.commit()
        h = {"Authorization": f"Bearer {_login(client, 'l@test.dev')}"}

        for aid in (draft.assessment_id, closed.assessment_id):
            r = client.post(
                f"/api/v1/assessments/{aid}/sessions", headers=h
            )
            assert r.status_code == 409
            assert r.json()["error"]["code"] == "assessment_not_active"
        assert client.post(
            "/api/v1/assessments/999999/sessions", headers=h
        ).status_code == 404

    def test_no_servable_questions_rejected_as_configuration(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        # unconfirmed AI tag → not servable; draft question → not servable
        _mcq(db_session, c, admin=admin, confirmed=False)
        _mcq(db_session, c, admin=admin, status="draft")
        a = _assessment(db_session, admin, [c])
        db_session.commit()
        h = {"Authorization": f"Bearer {_login(client, 'l@test.dev')}"}
        r = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "assessment_bank_incomplete"

    def test_difficulty_range_filters_pool(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        # only a diff-5 question exists but range is 1-2 → nothing servable
        _mcq(db_session, c, diff=5, admin=admin)
        a = _assessment(db_session, admin, [c], min_d=1, max_d=2)
        db_session.commit()
        h = {"Authorization": f"Bearer {_login(client, 'l@test.dev')}"}
        r = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "assessment_bank_incomplete"


class TestServeAndAdapt:
    def _bank(self, db, admin, concepts):
        """Three basic MCQs + harder items per concept + one sql + essay."""
        for c in concepts:
            for d in (1, 2, 3, 4):
                _mcq(db, c, diff=d, admin=admin,
                     prompt=f"{c.concept_code}-d{d}")
        _sql(db, concepts[0], admin=admin)
        _sql(db, concepts[1], admin=admin)
        _essay(db, concepts[2], admin=admin)

    def test_serve_next_is_idempotent(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        _mcq(db_session, c, admin=admin)
        a = _assessment(db_session, admin, [c])
        db_session.commit()
        token = _login(client, "l@test.dev")
        h = {"Authorization": f"Bearer {token}"}
        s = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        ).json()

        r1, r2 = _serve(client, token, s["session_id"]), _serve(
            client, token, s["session_id"])
        assert r1.json()["question"]["attempt_id"] == s["current_question"]["attempt_id"]
        assert r1.json() == r2.json()
        # still one attempt, one log row
        assert len(_logs(db_session, s["session_id"])) == 1

    def test_opening_phase_three_basic_mcqs(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c1, c2 = _concept(db_session, "C1"), _concept(db_session, "C2")
        _mcq(db_session, c1, diff=1, admin=admin, prompt="c1d1")
        _mcq(db_session, c2, diff=1, admin=admin, prompt="c2d1")
        _mcq(db_session, c1, diff=2, admin=admin, prompt="c1d2")
        _mcq(db_session, c1, diff=4, admin=admin, prompt="c1d4")
        a = _assessment(db_session, admin, [c1, c2])
        db_session.commit()
        token = _login(client, "l@test.dev")
        h = {"Authorization": f"Bearer {token}"}
        s = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        ).json()

        served = [s["current_question"]]
        for _ in range(2):
            _answer_current(client, token, s, db_session, correct=True)
            s2 = _serve(client, token, s["session_id"]).json()
            served.append(s2["question"])
            s = client.get(
                f"/api/v1/sessions/{s['session_id']}", headers=h
            ).json()
        # first three served: mcq difficulty ≤ 2, spread across concepts
        assert all(
            q["question_type"] == "mcq" and q["difficulty_level"] <= 2
            for q in served
        )
        prompts = {q["prompt"] for q in served}
        assert "c2d1" in prompts  # coverage spread to second concept
        logs = _logs(db_session, s["session_id"])
        assert len(logs) == 3
        assert all(l.decision_detail["phase"] == "opening" for l in logs)

    def test_difficulty_raises_after_clean_opening(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        for d in (1, 1, 2, 3, 4):
            _mcq(db_session, c, diff=d, admin=admin)
        a = _assessment(db_session, admin, [c])
        db_session.commit()
        token = _login(client, "l@test.dev")
        h = {"Authorization": f"Bearer {token}"}
        s = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        ).json()
        sid = s["session_id"]
        # answer all three openings correctly
        for _ in range(3):
            _answer_current(client, token, s, db_session, correct=True)
            nxt = _serve(client, token, sid).json()
            if nxt["question"] is None:
                break
            s = client.get(f"/api/v1/sessions/{sid}", headers=h).json()
        q4 = _logs(db_session, sid)[3].decision_detail
        assert q4["phase"] == "adaptive"
        assert q4["opening_correct"] == 3
        assert q4["opening_bias"] == 3
        assert q4["preferred_difficulty"] == 3

    def test_weak_probe_after_failed_opening(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c1, c2 = _concept(db_session, "C1"), _concept(db_session, "C2")
        for d in (1, 1, 2, 4):
            _mcq(db_session, c1, diff=d, admin=admin)
        _mcq(db_session, c2, diff=1, admin=admin)
        a = _assessment(db_session, admin, [c1, c2])
        db_session.commit()
        token = _login(client, "l@test.dev")
        h = {"Authorization": f"Bearer {token}"}
        s = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        ).json()
        sid = s["session_id"]
        for _ in range(3):
            _answer_current(client, token, s, db_session, correct=False)
            nxt = _serve(client, token, sid).json()
            if nxt["question"] is None:
                break
            s = client.get(f"/api/v1/sessions/{sid}", headers=h).json()
        q4 = _logs(db_session, sid)[3].decision_detail
        assert q4["opening_correct"] == 0
        assert q4["preferred_difficulty"] == 1

    def test_question_mix_quota_pressure(self, client, db_session):
        """Formal assessment: 13 questions, target 10 mcq / 2 sql / 1 essay —
        the mix must be reached even though mcq is the default."""
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        for d in (1, 1, 2):
            _mcq(db_session, c, diff=d, admin=admin)
        _sql(db_session, c, admin=admin)
        _sql(db_session, c, admin=admin)
        _essay(db_session, c, diff=2, admin=admin)
        a = _assessment(
            db_session, admin, [c]
        )
        db_session.commit()
        token = _login(client, "l@test.dev")
        h = {"Authorization": f"Bearer {token}"}

        class _StubLLM:
            def generate_structured(
                self, task_type, messages, *, json_schema=None, max_tokens=None, **kwargs
            ):
                return {
                    "rubric_level": "Complete", "score": 1.0,
                    "confidence": 0.9, "matched_criteria": [],
                    "missing_concepts": [], "evidence": [],
                    "explanation": "why", "feedback": "good",
                }

        app.dependency_overrides[get_llm_service] = lambda: _StubLLM()
        try:
            s = client.post(
                f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
            ).json()
            sid = s["session_id"]
            types = [s["current_question"]["question_type"]]
            for _ in range(12):
                cur = client.get(
                    f"/api/v1/sessions/{sid}", headers=h
                ).json()
                _answer_current(client, token, cur, db_session, correct=True)
                nxt = _serve(client, token, sid).json()
                if nxt["done"]:
                    break
                types.append(nxt["question"]["question_type"])
        finally:
            app.dependency_overrides.pop(get_llm_service, None)

        assert sorted(types) == sorted(
            ["mcq"] * 10 + ["sql", "sql", "essay"]
        )

    def test_done_when_max_questions_reached(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        for d in (1, 1, 2, 2):
            _mcq(db_session, c, diff=d, admin=admin)
        a = _assessment(
            db_session, admin, [c]
        )
        db_session.commit()
        token = _login(client, "l@test.dev")
        h = {"Authorization": f"Bearer {token}"}
        s = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        ).json()
        sid = s["session_id"]
        # Mark thirteen served items submitted to isolate the terminal-state
        # guard; full answer/grading traversal is covered by the mix journey.
        from datetime import datetime, timezone
        from app.services.evidence_context import capture_question
        from app.repositories import AssessmentRepository
        repo = AssessmentRepository(db_session)
        attempt = db_session.query(Attempt).filter_by(session_id=sid).one()
        attempt.submitted_at = datetime.now(timezone.utc)
        attempt.score = Decimal("1")
        attempt.grading_status = "graded"
        used = {attempt.question_id}
        for index, question in enumerate([q for q in db_session.query(Question).all() if q.question_id not in used][:12], start=2):
            added = repo.create_attempt(sid, question.question_id, index)
            added.question_snapshot = capture_question(repo, question)
            added.submitted_at = datetime.now(timezone.utc)
            added.score = Decimal("1")
            added.grading_status = "graded"
        db_session.commit()
        r = _serve(client, token, sid)
        assert r.json() == {"done": True, "question": None}
        state = client.get(f"/api/v1/sessions/{sid}", headers=h).json()
        assert state["done"] is True and state["served_count"] == 13

    def test_incomplete_pool_cannot_start_and_exhaust_early(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        _mcq(db_session, c, diff=1, admin=admin)  # only ONE servable item
        a = _assessment(db_session, admin, [c], max_q=13, complete=False)
        db_session.commit()
        token = _login(client, "l@test.dev")
        h = {"Authorization": f"Bearer {token}"}
        s = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        )
        assert s.status_code == 422
        assert s.json()["error"]["code"] == "assessment_bank_incomplete"


class TestOwnership:
    def test_other_learner_and_admin_blocked(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        _make_account(db_session, "other@test.dev", "Learner")
        c = _concept(db_session, "C1")
        _mcq(db_session, c, admin=admin)
        a = _assessment(db_session, admin, [c])
        db_session.commit()
        token = _login(client, "l@test.dev")
        s = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        sid = s["session_id"]

        other = {"Authorization": f"Bearer {_login(client, 'other@test.dev')}"}
        admin_h = {"Authorization": f"Bearer {_login(client, 'admin@test.dev')}"}
        assert client.get(f"/api/v1/sessions/{sid}", headers=other).status_code == 404
        assert client.post(
            f"/api/v1/sessions/{sid}/serve-next", headers=other
        ).status_code == 404
        assert client.post(
            f"/api/v1/sessions/{sid}/finish", headers=other
        ).status_code == 404
        assert client.get(
            f"/api/v1/sessions/{sid}/evidence", headers=other
        ).status_code == 404
        assert client.get(f"/api/v1/sessions/{sid}", headers=admin_h).status_code == 403
        assert client.get(f"/api/v1/sessions/{sid}").status_code == 401


class TestFinishAndEvidence:
    def test_finish_computes_and_locks(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        _mcq(db_session, c, diff=1, admin=admin)
        a = _assessment(db_session, admin, [c])
        db_session.commit()
        token = _login(client, "l@test.dev")
        h = {"Authorization": f"Bearer {token}"}
        s = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        ).json()
        sid = s["session_id"]
        _answer_current(client, token, s, db_session, correct=True)

        r = client.post(f"/api/v1/sessions/{sid}/finish", headers=h)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "completed"
        assert body["submitted_at"] is not None
        assert body["done"] is True

        # competency rows were persisted deterministically
        prof = client.get(
            f"/api/v1/sessions/{sid}/competency", headers=h
        )
        assert prof.status_code == 200
        # answering the only question correctly → 100% on C1
        row = next(
            i for i in prof.json()["concepts"] if i["concept_id"] == c.concept_id
        )
        assert Decimal(row["competency_pct"]) == Decimal("100.00")

        # session is locked for further answers
        r2 = _serve(client, token, sid)
        assert r2.status_code == 409

    def test_pending_attempt_counts_as_no_evidence(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        _mcq(db_session, c, diff=1, admin=admin)
        a = _assessment(db_session, admin, [c])
        db_session.commit()
        token = _login(client, "l@test.dev")
        h = {"Authorization": f"Bearer {token}"}
        s = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        ).json()
        sid = s["session_id"]
        # finish WITHOUT answering the pending question
        client.post(f"/api/v1/sessions/{sid}/finish", headers=h)
        prof = client.get(
            f"/api/v1/sessions/{sid}/competency", headers=h
        ).json()
        assert prof["concepts"] == []  # served-not-answered → no evidence

    def test_timeout_flips_to_timed_out(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        learner = _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        _mcq(db_session, c, admin=admin)
        a = _assessment(db_session, admin, [c])
        db_session.commit()
        token = _login(client, "l@test.dev")
        h = {"Authorization": f"Bearer {token}"}
        s = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        ).json()
        sid = s["session_id"]

        # move expiry into the past
        sess = db_session.get(AssessmentSession, sid)
        sess.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db_session.commit()

        state = client.get(f"/api/v1/sessions/{sid}", headers=h).json()
        assert state["status"] == "timed_out"
        assert _serve(client, token, sid).status_code == 409
        assert _serve(client, token, sid).json()["error"]["code"] in (
            "session_expired", "session_not_active",
        )

    def test_evidence_records(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        c = _concept(db_session, "C1")
        q = _mcq(db_session, c, diff=1, admin=admin)
        a = _assessment(db_session, admin, [c])
        db_session.commit()
        token = _login(client, "l@test.dev")
        h = {"Authorization": f"Bearer {token}"}
        s = client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        ).json()
        sid = s["session_id"]

        # evidence is not readable while the session is still running
        assert client.get(
            f"/api/v1/sessions/{sid}/evidence", headers=h
        ).status_code == 409

        _answer_current(client, token, s, db_session, correct=True)
        client.post(f"/api/v1/sessions/{sid}/finish", headers=h)

        r = client.get(f"/api/v1/sessions/{sid}/evidence", headers=h)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "completed"
        assert len(body["items"]) == 1
        item = body["items"][0]
        assert item["question_id"] == q.question_id
        assert item["question_type"] == "mcq"
        assert item["seq_no"] == 1
        assert item["submitted_at"] is not None
        assert item["grading_detail"]["is_correct"] is True
        assert item["selected_option_id"] is not None
        # answer key revealed only post-finalization
        assert any(o["is_correct"] for o in item["options"])
        assert item["concepts"][0]["concept_id"] == c.concept_id

    def test_rbac_learners_only(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c = _concept(db_session, "C1")
        _mcq(db_session, c, admin=admin)
        a = _assessment(db_session, admin, [c])
        db_session.commit()
        h = {"Authorization": f"Bearer {_login(client, 'admin@test.dev')}"}
        assert client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions", headers=h
        ).status_code == 403
        assert client.post(
            f"/api/v1/assessments/{a.assessment_id}/sessions"
        ).status_code == 401
