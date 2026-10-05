"""UC06 / UC08 / UC10 — AI-assisted admin curation tests.

The LLM is stubbed at the ``get_llm_service`` dependency — no provider
calls. The suite verifies the assistive-only contract: AI suggestions
land pending/unconfirmed and cannot affect serving or the bank until an
administrator acts, and UC10 promotion runs the deterministic
completeness/duplicate/SQL-execution checks.
"""

from decimal import Decimal

from app.deps import get_llm_service
from app.main import app
from app.models import (
    Account,
    AccountRole,
    Concept,
    CourseLearningOutcome,
    CloConcept,
    McqOption,
    Question,
    QuestionConcept,
    Role,
    SqlTestDataset,
    UserProfile,
)
from app.security import hash_password

BASE = "/api/v1/admin"


class StubLLM:
    """Canned structured responses; records the prompts it received."""

    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate_structured(
        self, task_type, messages, *, json_schema=None, max_tokens=None
    ):
        self.calls.append(task_type)
        return self.response


def _use_llm(response):
    app.dependency_overrides[get_llm_service] = lambda: StubLLM(response)


def _clear_llm():
    app.dependency_overrides.pop(get_llm_service, None)


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


def _admin(client, db):
    """Headers for admin@test.dev — creates the account only if the test
    has not already (tests needing the Account object create it first)."""
    if not db.query(Account).filter_by(email="admin@test.dev").count():
        _make_account(db, "admin@test.dev", "Administrator")
    return {"Authorization": f"Bearer {_login(client, 'admin@test.dev')}"}


def _concept(db, code):
    c = Concept(
        concept_code=code, concept_name=code, subject_area="SQL Querying",
        difficulty_level=2,
    )
    db.add(c)
    db.flush()
    return c


def _clo(db, admin, code="CLO-1"):
    clo = CourseLearningOutcome(
        clo_code=code, title="Write queries", created_by=admin.account_id
    )
    db.add(clo)
    db.flush()
    return clo


def _mcq_question(db, admin, *, prompt="What is a primary key?", status="draft",
                  confirmed_tag=None):
    q = Question(
        question_type="mcq", prompt=prompt, difficulty_level=1,
        points=Decimal("1.0"), status=status, created_by=admin.account_id,
    )
    db.add(q)
    db.flush()
    db.add(McqOption(question_id=q.question_id, option_label="A",
                     option_text="pk", is_correct=True))
    db.add(McqOption(question_id=q.question_id, option_label="B",
                     option_text="fk", is_correct=False))
    if confirmed_tag is not None:
        db.add(QuestionConcept(question_id=q.question_id,
                               concept_id=confirmed_tag, confirmed=True))
    db.flush()
    return q


# ---------------------------------------------------------------- UC06


class TestCloAiSuggest:
    def test_suggest_stores_pending_links(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c1, c2 = _concept(db_session, "C1"), _concept(db_session, "C2")
        clo = _clo(db_session, admin)
        db_session.commit()
        h = _admin(client, db_session)

        _use_llm({"concept_ids": [c1.concept_id, c2.concept_id, 999999],
                  "rationale": "both fit"})
        try:
            r = client.post(
                f"{BASE}/clos/{clo.clo_id}/ai-suggest", headers=h
            )
        finally:
            _clear_llm()
        assert r.status_code == 200, r.json()
        body = r.json()
        assert sorted(body["suggested_concept_ids"]) == sorted(
            [c1.concept_id, c2.concept_id]
        )
        assert body["ignored_concept_ids"] == [999999]
        links = {l["concept_id"]: l for l in body["clo"]["concepts"]}
        assert links[c1.concept_id]["mapping_source"] == "ai"
        assert links[c1.concept_id]["status"] == "pending"

    def test_pending_ai_links_never_downgrade_confirmed(
        self, client, db_session
    ):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c1 = _concept(db_session, "C1")
        clo = _clo(db_session, admin)
        db_session.add(
            CloConcept(clo_id=clo.clo_id, concept_id=c1.concept_id,
                       mapping_source="admin", status="confirmed")
        )
        db_session.commit()
        h = _admin(client, db_session)
        _use_llm({"concept_ids": [c1.concept_id], "rationale": "re-suggest"})
        try:
            r = client.post(
                f"{BASE}/clos/{clo.clo_id}/ai-suggest", headers=h
            )
        finally:
            _clear_llm()
        body = r.json()
        assert body["suggested_concept_ids"] == []
        link = body["clo"]["concepts"][0]
        assert link["status"] == "confirmed"  # unchanged

    def test_confirm_and_reject(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c1, c2 = _concept(db_session, "C1"), _concept(db_session, "C2")
        clo = _clo(db_session, admin)
        for c in (c1, c2):
            db_session.add(
                CloConcept(clo_id=clo.clo_id, concept_id=c.concept_id,
                           mapping_source="ai", status="pending")
            )
        db_session.commit()
        h = _admin(client, db_session)

        ok = client.post(
            f"{BASE}/clos/{clo.clo_id}/concepts/{c1.concept_id}/confirm",
            headers=h,
        )
        assert ok.status_code == 200
        link = next(
            l for l in ok.json()["concepts"] if l["concept_id"] == c1.concept_id
        )
        assert link["status"] == "confirmed"
        assert link["mapping_source"] == "ai"  # provenance kept

        rej = client.delete(
            f"{BASE}/clos/{clo.clo_id}/concepts/{c2.concept_id}", headers=h
        )
        assert rej.status_code == 200
        assert [l["concept_id"] for l in rej.json()["concepts"]] == [
            c1.concept_id
        ]

        # confirmed rows cannot be removed through the reject path
        assert client.delete(
            f"{BASE}/clos/{clo.clo_id}/concepts/{c1.concept_id}", headers=h
        ).status_code == 409

    def test_rbac(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        _make_account(db_session, "l@test.dev", "Learner")
        clo = _clo(db_session, admin)
        db_session.commit()
        h = {"Authorization": f"Bearer {_login(client, 'l@test.dev')}"}
        assert client.post(
            f"{BASE}/clos/{clo.clo_id}/ai-suggest", headers=h
        ).status_code == 403


# ---------------------------------------------------------------- UC08


class TestQuestionAiTags:
    def test_suggest_stores_unconfirmed_ai_tags(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c1, c2 = _concept(db_session, "C1"), _concept(db_session, "C2")
        q = _mcq_question(db_session, admin)
        db_session.commit()
        h = _admin(client, db_session)

        _use_llm({
            "concept_ids": [c1.concept_id, c2.concept_id, 424242],
            "difficulty_level": 3,
            "evaluation_criteria": "identifies unique row keys",
        })
        try:
            r = client.post(
                f"{BASE}/questions/{q.question_id}/ai-tags", headers=h
            )
        finally:
            _clear_llm()
        assert r.status_code == 200, r.json()
        body = r.json()
        assert sorted(body["suggested_concept_ids"]) == sorted(
            [c1.concept_id, c2.concept_id]
        )
        assert body["ignored_concept_ids"] == [424242]
        assert body["suggested_difficulty"] == 3
        assert body["evaluation_criteria"] == "identifies unique row keys"
        tags = {
            t["concept_id"]: t for t in body["question"]["concepts"]
        }
        assert tags[c1.concept_id]["tag_source"] == "ai"
        assert tags[c1.concept_id]["confirmed"] is False

    def test_unconfirmed_ai_tags_cannot_validate(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c1 = _concept(db_session, "C1")
        q = _mcq_question(db_session, admin)
        db_session.commit()
        h = _admin(client, db_session)

        _use_llm({"concept_ids": [c1.concept_id]})
        try:
            client.post(f"{BASE}/questions/{q.question_id}/ai-tags", headers=h)
        finally:
            _clear_llm()
        # an unconfirmed ai tag does NOT satisfy the validated checklist
        r = client.patch(
            f"{BASE}/questions/{q.question_id}",
            json={"status": "validated"}, headers=h,
        )
        assert r.status_code == 422

        # confirming the tag makes validation pass
        ok = client.post(
            f"{BASE}/questions/{q.question_id}/tags/{c1.concept_id}/confirm",
            headers=h,
        )
        assert ok.status_code == 200
        tag = next(
            t for t in ok.json()["concepts"] if t["concept_id"] == c1.concept_id
        )
        assert tag["confirmed"] is True
        r2 = client.patch(
            f"{BASE}/questions/{q.question_id}",
            json={"status": "validated"}, headers=h,
        )
        assert r2.status_code == 200

        # confirmed tags cannot be removed through the reject path
        assert client.delete(
            f"{BASE}/questions/{q.question_id}/tags/{c1.concept_id}",
            headers=h,
        ).status_code == 409

    def test_reject_pending_tag(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c1 = _concept(db_session, "C1")
        q = _mcq_question(db_session, admin)
        db_session.add(
            QuestionConcept(question_id=q.question_id,
                            concept_id=c1.concept_id, tag_source="ai",
                            confirmed=False)
        )
        db_session.commit()
        h = _admin(client, db_session)
        r = client.delete(
            f"{BASE}/questions/{q.question_id}/tags/{c1.concept_id}",
            headers=h,
        )
        assert r.status_code == 200
        assert r.json()["concepts"] == []


# ---------------------------------------------------------------- UC10


class TestCandidates:
    def _gen(self, client, h, concept_id, qtype="mcq", count=1):
        return client.post(
            f"{BASE}/question-candidates/generate",
            json={"concept_id": concept_id, "question_type": qtype,
                  "count": count},
            headers=h,
        )

    def test_generate_validates_good_mcq(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c1 = _concept(db_session, "C1")
        db_session.commit()
        h = _admin(client, db_session)

        _use_llm({"questions": [{
            "prompt": "Which constraint enforces uniqueness?",
            "options": [
                {"option_label": "A", "option_text": "UNIQUE",
                 "is_correct": True},
                {"option_label": "B", "option_text": "INDEX",
                 "is_correct": False},
            ],
            "difficulty_level": 2,
        }]})
        try:
            r = self._gen(client, h, c1.concept_id)
        finally:
            _clear_llm()
        assert r.status_code == 201, r.json()
        cand = r.json()[0]
        assert cand["validation_status"] == "validated"
        assert cand["validation_detail"]["ok"] is True
        checks = {c["check"]: c for c in cand["validation_detail"]["checks"]}
        assert checks["completeness"]["ok"] is True
        assert checks["duplicate"]["ok"] is True

    def test_incomplete_payload_stays_pending(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c1 = _concept(db_session, "C1")
        db_session.commit()
        h = _admin(client, db_session)
        _use_llm({"questions": [{"prompt": "", "options": []}]})
        try:
            r = self._gen(client, h, c1.concept_id)
        finally:
            _clear_llm()
        cand = r.json()[0]
        assert cand["validation_status"] == "pending"
        completeness = next(
            c for c in cand["validation_detail"]["checks"]
            if c["check"] == "completeness"
        )
        assert completeness["ok"] is False
        # cannot be approved while pending
        r2 = client.post(
            f"{BASE}/question-candidates/{cand['candidate_id']}/approve",
            headers=h,
        )
        assert r2.status_code == 409
        assert r2.json()["error"]["code"] == "candidate_not_validated"

    def test_duplicate_prompt_detected(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c1 = _concept(db_session, "C1")
        _mcq_question(
            db_session, admin, prompt="What is a primary key?",
            status="validated", confirmed_tag=c1.concept_id,
        )
        db_session.commit()
        h = _admin(client, db_session)
        _use_llm({"questions": [{
            "prompt": "  What is a  PRIMARY key? ",  # normalized duplicate
            "options": [
                {"option_label": "A", "option_text": "x", "is_correct": True},
                {"option_label": "B", "option_text": "y", "is_correct": False},
            ],
            "difficulty_level": 1,
        }]})
        try:
            r = self._gen(client, h, c1.concept_id)
        finally:
            _clear_llm()
        cand = r.json()[0]
        assert cand["validation_status"] == "pending"
        dup = next(
            c for c in cand["validation_detail"]["checks"]
            if c["check"] == "duplicate"
        )
        assert dup["ok"] is False and dup["matches"]

    def test_approve_promotes_to_validated_bank_item(
        self, client, db_session
    ):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c1 = _concept(db_session, "C1")
        db_session.commit()
        h = _admin(client, db_session)
        _use_llm({"questions": [{
            "prompt": "What does ACID stand for?",
            "options": [
                {"option_label": "A", "option_text": "a", "is_correct": True},
                {"option_label": "B", "option_text": "b", "is_correct": False},
            ],
            "difficulty_level": 2,
        }]})
        try:
            cand = self._gen(client, h, c1.concept_id).json()[0]
        finally:
            _clear_llm()
        assert cand["validation_status"] == "validated"

        r = client.post(
            f"{BASE}/question-candidates/{cand['candidate_id']}/approve",
            headers=h,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["validation_status"] == "approved"
        qid = body["promoted_question_id"]
        assert qid is not None

        # the promoted item is a real validated question, ai-sourced
        detail = client.get(f"{BASE}/questions/{qid}", headers=h).json()
        assert detail["status"] == "validated"
        assert detail["source"] == "ai"
        assert detail["concepts"][0]["tag_source"] == "ai"
        assert detail["concepts"][0]["confirmed"] is True
        assert len(detail["options"]) == 2

        # approve is idempotent
        again = client.post(
            f"{BASE}/question-candidates/{cand['candidate_id']}/approve",
            headers=h,
        )
        assert again.status_code == 200
        assert again.json()["promoted_question_id"] == qid

    def test_sql_candidate_execution_check(self, client, db_session):
        """UC10 requires the reference answer to actually run on the
        declared datasets in the sandbox before review."""
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c1 = _concept(db_session, "C1")
        db_session.commit()
        h = _admin(client, db_session)

        good = {
            "prompt": "Select all ids.",
            "reference_answer": "SELECT id FROM t",
            "datasets": [{
                "dataset_name": "d1",
                "setup_sql": "CREATE TABLE t (id int);"
                             " INSERT INTO t VALUES (1);",
                "expected_result": {"rows": [[1]], "columns": ["id"]},
                "is_edge_case": False,
            }],
            "difficulty_level": 2,
        }
        _use_llm({"questions": [good]})
        try:
            r = self._gen(client, h, c1.concept_id, qtype="sql")
        finally:
            _clear_llm()
        cand = r.json()[0]
        assert cand["validation_status"] == "validated", cand
        sql_check = next(
            c for c in cand["validation_detail"]["checks"]
            if c["check"] == "sql_execution"
        )
        assert sql_check["ok"] is True

        # wrong expected result → check fails → pending
        bad = dict(good, prompt="Select every id, variant B.")
        bad["datasets"] = [dict(good["datasets"][0],
                                expected_result={"rows": [[9]],
                                                 "columns": ["id"]})]
        _use_llm({"questions": [bad]})
        try:
            r2 = self._gen(client, h, c1.concept_id, qtype="sql")
        finally:
            _clear_llm()
        cand2 = r2.json()[0]
        assert cand2["validation_status"] == "pending"
        sql_check2 = next(
            c for c in cand2["validation_detail"]["checks"]
            if c["check"] == "sql_execution"
        )
        assert sql_check2["ok"] is False

    def test_reject_hides_from_queue(self, client, db_session):
        admin = _make_account(db_session, "admin@test.dev", "Administrator")
        c1 = _concept(db_session, "C1")
        db_session.commit()
        h = _admin(client, db_session)
        _use_llm({"questions": [{
            "prompt": "P?", "options": [
                {"option_label": "A", "option_text": "x", "is_correct": True},
                {"option_label": "B", "option_text": "y", "is_correct": False},
            ],
        }]})
        try:
            cand = self._gen(client, h, c1.concept_id).json()[0]
        finally:
            _clear_llm()
        client.post(
            f"{BASE}/question-candidates/{cand['candidate_id']}/reject",
            headers=h,
        )
        listing = client.get(
            f"{BASE}/question-candidates", headers=h
        ).json()
        assert listing == []
        rejected = client.get(
            f"{BASE}/question-candidates?status=rejected", headers=h
        ).json()
        assert len(rejected) == 1

    def test_rbac(self, client, db_session):
        _make_account(db_session, "l@test.dev", "Learner")
        db_session.commit()
        h = {"Authorization": f"Bearer {_login(client, 'l@test.dev')}"}
        assert client.get(
            f"{BASE}/question-candidates", headers=h
        ).status_code == 403
        assert client.post(
            f"{BASE}/question-candidates/generate",
            json={"concept_id": 1, "question_type": "mcq"}, headers=h,
        ).status_code == 403
