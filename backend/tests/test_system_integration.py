"""DBCAS-28 — system integration journeys through HTTP only.

These tests drive the API exactly the way the frontend does: account
provisioning → curriculum setup → question bank → assessment activation
→ adaptive session → grading → competency/gaps/guidance → history +
evidence → cohort analytics. ORM access is used only to seed the
bootstrap administrator and to assert audit internals that have no API
surface (selection_log).
"""

import pytest

from app.main import app
from app.deps import get_llm_service
from app.models import (
    Account,
    AccountRole,
    Role,
    SelectionLog,
    UserProfile,
)
from app.security import hash_password

ADMIN_PW = "Admin123!"
LEARNER_PW = "Learner123!"


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _bootstrap_admin(db, email="root@test.dev"):
    """The first administrator can only come from provisioning — the rest
    of the journey uses the UC04 API."""
    account = Account(
        email=email, password_hash=hash_password(ADMIN_PW), status="active"
    )
    account.profile = UserProfile(full_name="Root Admin")
    role = db.query(Role).filter_by(role_name="Administrator").one()
    db.add(account)
    db.flush()
    db.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db.commit()
    return account


def _login(client, email, password):
    r = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200, r.json()
    return r.json()["access_token"]


def _register(client, email, name, password=LEARNER_PW):
    r = client.post(
        "/api/v1/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
            "password_confirm": password,
        },
    )
    assert r.status_code in (200, 201), r.json()
    return r


def _make_concept(client, admin, code):
    r = client.post(
        "/api/v1/admin/concepts",
        headers=_h(admin),
        json={
            "concept_code": code,
            "concept_name": f"{code} name",
            "subject_area": "SQL Querying",
            "difficulty_level": 2,
        },
    )
    assert r.status_code == 201, r.json()
    return r.json()["concept_id"]


def _make_mcq(client, admin, concept_id, prompt, diff=1):
    r = client.post(
        "/api/v1/admin/questions",
        headers=_h(admin),
        json={
            "question_type": "mcq",
            "prompt": prompt,
            "difficulty_level": diff,
            "points": "1.0",
            "concept_ids": [concept_id],
            "options": [
                {"option_label": "A", "option_text": "correct", "is_correct": True},
                {"option_label": "B", "option_text": "wrong", "is_correct": False},
            ],
        },
    )
    assert r.status_code == 201, r.json()
    qid = r.json()["question_id"]
    r = client.patch(
        f"/api/v1/admin/questions/{qid}",
        headers=_h(admin),
        json={"status": "validated"},
    )
    assert r.status_code == 200, r.json()
    return qid


def _make_sql(client, admin, concept_id):
    r = client.post(
        "/api/v1/admin/questions",
        headers=_h(admin),
        json={
            "question_type": "sql",
            "prompt": "List every row of t.",
            "reference_answer": "SELECT id FROM t ORDER BY id",
            "difficulty_level": 2,
            "points": "2.0",
            "concept_ids": [concept_id],
            "datasets": [
                {
                    "dataset_name": "base",
                    "setup_sql": "CREATE TABLE t (id int);"
                    " INSERT INTO t VALUES (1), (2);",
                    "expected_result": {"columns": ["id"], "rows": [[1], [2]]},
                    "is_edge_case": False,
                }
            ],
        },
    )
    assert r.status_code == 201, r.json()
    qid = r.json()["question_id"]
    r = client.patch(
        f"/api/v1/admin/questions/{qid}",
        headers=_h(admin),
        json={"status": "validated"},
    )
    assert r.status_code == 200, r.json()
    return qid


def _answer(client, token, session_id, question, correct):
    payload = {"question_id": question["question_id"]}
    if question["question_type"] == "mcq":
        label = "A" if correct else "B"
        opt = next(
            o for o in question["options"] if o["option_label"] == label
        )
        payload["selected_option_id"] = opt["option_id"]
    elif question["question_type"] == "sql":
        payload["sql_answer"] = "SELECT id FROM t ORDER BY id"
    else:
        payload["essay_answer"] = "A complete explanation."
    r = client.post(
        f"/api/v1/sessions/{session_id}/answers",
        headers=_h(token),
        json=payload,
    )
    assert r.status_code == 200, r.json()
    return r.json()


# ------------------------------------------------------------------- tests


def test_learner_end_to_end_journey(client, db_session):
    """The flagship path: admin configures everything through the admin
    API, the learner registers, takes an adaptive session, and both sides
    see the deterministic results."""
    _bootstrap_admin(db_session)
    admin = _login(client, "root@test.dev", ADMIN_PW)

    # --- admin: curriculum, bank, assessment config (all via API) ---
    c1 = _make_concept(client, admin, "SQL-SELECT")
    c2 = _make_concept(client, admin, "SQL-WHERE")
    for i in range(3):
        _make_mcq(client, admin, c1, f"Basic MCQ {i}", diff=1)
    _make_sql(client, admin, c2)

    r = client.post(
        "/api/v1/admin/assessments",
        headers=_h(admin),
        json={
            "title": "Midterm",
            "description": "adaptive",
            "max_questions": 4,
            "duration_min": 60,
            "target_mcq": 3,
            "target_sql": 1,
            "target_essay": 0,
            "concepts": [
                {
                    "concept_id": c1,
                    "min_difficulty": 1,
                    "max_difficulty": 5,
                    "target_pct": "60.00",
                },
                {
                    "concept_id": c2,
                    "min_difficulty": 1,
                    "max_difficulty": 5,
                    "target_pct": "60.00",
                },
            ],
        },
    )
    assert r.status_code == 201, r.json()
    assessment_id = r.json()["assessment_id"]
    r = client.patch(
        f"/api/v1/admin/assessments/{assessment_id}",
        headers=_h(admin),
        json={"status": "active"},
    )
    assert r.status_code == 200, r.json()

    # --- learner: register, discover, start ---
    _register(client, "learner@test.dev", "Learner One")
    learner = _login(client, "learner@test.dev", LEARNER_PW)

    r = client.get("/api/v1/assessments", headers=_h(learner))
    assert r.status_code == 200
    assert [a["assessment_id"] for a in r.json()] == [assessment_id]

    r = client.post(
        f"/api/v1/assessments/{assessment_id}/sessions", headers=_h(learner)
    )
    assert r.status_code == 201, r.json()
    sid = r.json()["session_id"]
    state = r.json()

    # --- the exam loop, answered the way ExamPage does ---
    mcq_correct = 0
    for _ in range(6):  # max 4 + margin
        q = state.get("current_question")
        if q is None:
            break
        # fail the SELECT concept, ace the WHERE sql question
        correct = q["question_type"] != "mcq"
        result = _answer(client, learner, sid, q, correct)
        assert result["submitted_at"] is not None
        if q["question_type"] == "mcq" and result["is_correct"]:
            mcq_correct += 1
        nxt = client.post(
            f"/api/v1/sessions/{sid}/serve-next", headers=_h(learner)
        ).json()
        state = client.get(f"/api/v1/sessions/{sid}", headers=_h(learner)).json()
        if nxt["done"]:
            break
    assert mcq_correct == 0  # deliberately bombed the MCQs

    r = client.post(f"/api/v1/sessions/{sid}/finish", headers=_h(learner))
    assert r.status_code == 200, r.json()
    assert r.json()["status"] == "completed"

    # --- history, evidence, competency, gaps, guidance ---
    history = client.get("/api/v1/sessions", headers=_h(learner)).json()
    assert history[0]["session_id"] == sid
    assert history[0]["status"] == "completed"
    assert history[0]["answered_count"] == 4

    ev = client.get(
        f"/api/v1/sessions/{sid}/evidence", headers=_h(learner)
    ).json()
    assert len(ev["items"]) == 4
    mcq_item = next(i for i in ev["items"] if i["question_type"] == "mcq")
    # grading key is revealed only now that the session is finalized
    assert "is_correct" in mcq_item["options"][0]
    sql_item = next(i for i in ev["items"] if i["question_type"] == "sql")
    assert sql_item["sql_answer"] == "SELECT id FROM t ORDER BY id"

    prof = client.get(
        f"/api/v1/sessions/{sid}/competency", headers=_h(learner)
    ).json()
    by_code = {c["concept_code"]: c for c in prof["concepts"]}
    assert by_code["SQL-SELECT"]["below_target"] is True
    assert by_code["SQL-WHERE"]["below_target"] is False

    gaps = client.get(
        f"/api/v1/sessions/{sid}/gaps", headers=_h(learner)
    ).json()
    assert [g["concept_code"] for g in gaps["gaps"]] == ["SQL-SELECT"]

    guide = client.get(
        f"/api/v1/sessions/{sid}/guidance", headers=_h(learner)
    ).json()
    assert guide["guidance"][0]["concept_code"] == "SQL-SELECT"
    assert guide["guidance"][0]["ready"] is True

    # every serve was audited
    logs = (
        db_session.query(SelectionLog)
        .filter_by(session_id=sid)
        .order_by(SelectionLog.seq_no)
        .all()
    )
    assert len(logs) == 4

    # --- admin sees the cohort result ---
    cohort = client.get("/api/v1/admin/analytics/cohort", headers=_h(admin)).json()
    assert cohort["learner_count"] == 1
    assert cohort["finalized_sessions"] == 1
    weakest = [c["concept_code"] for c in cohort["weakest_concepts"]]
    assert "SQL-SELECT" in weakest

    drill = client.get(
        "/api/v1/admin/learners", headers=_h(admin)
    ).json()
    lid = drill[0]["account_id"]
    sessions = client.get(
        f"/api/v1/admin/learners/{lid}/sessions", headers=_h(admin)
    ).json()
    assert sessions["sessions"][0]["session_id"] == sid


def test_admin_provisioning_and_ai_curation_journey(client, db_session):
    """UC04 + UC06/08/10: provision a second admin, then run the whole
    AI-assist pipeline — suggestions stay pending until confirmed, and a
    generated candidate only reaches the bank via approval."""
    _bootstrap_admin(db_session)
    root = _login(client, "root@test.dev", ADMIN_PW)

    # --- UC04: provision → disabled → cannot log in → activate → can ---
    r = client.post(
        "/api/v1/admin/accounts",
        headers=_h(root),
        json={
            "name": "Second Admin",
            "email": "second@test.dev",
            "password": "Second123!",
            "role": "Administrator",
        },
    )
    assert r.status_code == 201, r.json()
    second_id = r.json()["account_id"]
    assert r.json()["status"] == "disabled"

    r = client.post(
        "/api/v1/auth/login",
        json={"email": "second@test.dev", "password": "Second123!"},
    )
    assert r.status_code == 403

    r = client.patch(
        f"/api/v1/admin/accounts/{second_id}",
        headers=_h(root),
        json={"status": "active"},
    )
    assert r.status_code == 200
    second = _login(client, "second@test.dev", "Second123!")

    # --- curriculum setup by the NEW admin ---
    cid = _make_concept(client, second, "SQL-JOIN")
    r = client.post(
        "/api/v1/admin/clos",
        headers=_h(second),
        json={"clo_code": "CLO1", "title": "Write joins"},
    )
    assert r.status_code == 201, r.json()
    clo_id = r.json()["clo_id"]

    class _StubLLM:
        def generate_structured(self, task_type, messages, **kw):
            if task_type == "clo_map":
                return {"concept_ids": [cid, 99999], "rationale": "fits"}
            if task_type == "tag":
                return {
                    "concept_ids": [cid],
                    "difficulty_level": 2,
                    "evaluation_criteria": "correct join syntax",
                }
            if task_type == "gen_question":
                return {
                    "questions": [
                        {
                            "prompt": "Drafted MCQ on joins",
                            "options": [
                                {
                                    "option_label": "A",
                                    "option_text": "INNER JOIN",
                                    "is_correct": True,
                                },
                                {
                                    "option_label": "B",
                                    "option_text": "OUTER SELECT",
                                    "is_correct": False,
                                },
                            ],
                            "difficulty_level": 2,
                        }
                    ]
                }
            return {}

    app.dependency_overrides[get_llm_service] = lambda: _StubLLM()
    try:
        # --- UC06: AI link lands pending, unknown ids are ignored ---
        r = client.post(
            f"/api/v1/admin/clos/{clo_id}/ai-suggest", headers=_h(second)
        )
        assert r.status_code == 200, r.json()
        body = r.json()
        assert body["suggested_concept_ids"] == [cid]
        assert body["ignored_concept_ids"] == [99999]
        link = body["clo"]["concepts"][0]
        assert link["status"] == "pending" and link["mapping_source"] == "ai"

        r = client.post(
            f"/api/v1/admin/clos/{clo_id}/concepts/{cid}/confirm",
            headers=_h(second),
        )
        assert r.status_code == 200
        assert r.json()["concepts"][0]["status"] == "confirmed"

        # --- UC08: AI tags on a bank question land pending ---
        # an untagged draft so the AI suggestion is the only tag
        r = client.post(
            "/api/v1/admin/questions",
            headers=_h(second),
            json={
                "question_type": "mcq",
                "prompt": "Bank question",
                "difficulty_level": 1,
                "points": "1.0",
                "options": [
                    {"option_label": "A", "option_text": "x", "is_correct": True},
                    {"option_label": "B", "option_text": "y", "is_correct": False},
                ],
            },
        )
        assert r.status_code == 201, r.json()
        qid = r.json()["question_id"]

        r = client.post(
            f"/api/v1/admin/questions/{qid}/ai-tags", headers=_h(second)
        )
        assert r.status_code == 200, r.json()
        assert r.json()["suggested_concept_ids"] == [cid]
        tag = r.json()["question"]["concepts"][0]
        assert tag["confirmed"] is False and tag["tag_source"] == "ai"

        r = client.post(
            f"/api/v1/admin/questions/{qid}/tags/{cid}/confirm",
            headers=_h(second),
        )
        assert r.status_code == 200
        assert r.json()["concepts"][0]["confirmed"] is True

        # --- UC10: generate → checks → approve → in the bank ---
        r = client.post(
            "/api/v1/admin/question-candidates/generate",
            headers=_h(second),
            json={"concept_id": cid, "question_type": "mcq", "count": 1},
        )
        assert r.status_code == 201, r.json()
        cand = r.json()[0]
        assert cand["validation_status"] == "validated"
        assert cand["validation_detail"]["ok"] is True

        r = client.post(
            f"/api/v1/admin/question-candidates/{cand['candidate_id']}/approve",
            headers=_h(second),
        )
        assert r.status_code == 200, r.json()
        assert r.json()["promoted_question_id"] is not None
    finally:
        app.dependency_overrides.pop(get_llm_service, None)

    promoted = client.get(
        "/api/v1/admin/questions",
        headers=_h(second),
        params={"status": "validated"},
    ).json()
    assert any(q["source"] == "ai" for q in promoted)


def test_isolation_and_rbac_boundaries(client, db_session):
    """A learner can only ever see their own session surface, and no
    learner token reaches an admin route."""
    _bootstrap_admin(db_session)
    admin = _login(client, "root@test.dev", ADMIN_PW)
    cid = _make_concept(client, admin, "SQL-SELECT")
    _make_mcq(client, admin, cid, "MCQ", diff=1)
    r = client.post(
        "/api/v1/admin/assessments",
        headers=_h(admin),
        json={
            "title": "A",
            "max_questions": 2,
            "duration_min": 30,
            "target_mcq": 1,
            "target_sql": 0,
            "target_essay": 0,
            "concepts": [{"concept_id": cid, "target_pct": "60.00"}],
        },
    )
    aid = r.json()["assessment_id"]
    client.patch(
        f"/api/v1/admin/assessments/{aid}",
        headers=_h(admin),
        json={"status": "active"},
    )

    _register(client, "a@test.dev", "A")
    _register(client, "b@test.dev", "B")
    tok_a = _login(client, "a@test.dev", LEARNER_PW)
    tok_b = _login(client, "b@test.dev", LEARNER_PW)

    sid = client.post(
        f"/api/v1/assessments/{aid}/sessions", headers=_h(tok_a)
    ).json()["session_id"]

    # learner B cannot reach A's session anywhere
    for method, path in (
        ("get", f"/api/v1/sessions/{sid}"),
        ("post", f"/api/v1/sessions/{sid}/serve-next"),
        ("post", f"/api/v1/sessions/{sid}/finish"),
        ("get", f"/api/v1/sessions/{sid}/evidence"),
        ("get", f"/api/v1/sessions/{sid}/competency"),
        ("get", f"/api/v1/sessions/{sid}/gaps"),
        ("get", f"/api/v1/sessions/{sid}/guidance"),
    ):
        r = getattr(client, method)(path, headers=_h(tok_b))
        assert r.status_code == 404, (method, path, r.status_code)

    # B's history does not contain A's session
    assert client.get("/api/v1/sessions", headers=_h(tok_b)).json() == []

    # a learner token reaches no admin route
    for method, path in (
        ("get", "/api/v1/admin/accounts"),
        ("get", "/api/v1/admin/questions"),
        ("get", "/api/v1/admin/assessments"),
        ("get", "/api/v1/admin/analytics/cohort"),
        ("get", "/api/v1/admin/question-candidates"),
    ):
        r = getattr(client, method)(path, headers=_h(tok_a))
        assert r.status_code == 403, (method, path, r.status_code)
