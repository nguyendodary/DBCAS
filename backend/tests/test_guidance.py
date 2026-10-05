"""Personalized study guidance tests — Task 5.2 (DBCAS-27).

Guidance = the documented "What to study next" list refined by the
prerequisite skill graph: gap concepts are sequenced prerequisite-first
(topological order over the gap subgraph); among unblocked concepts the
larger shortfall still ranks first and concept_id breaks ties. The LLM
explanation mechanism is identical to the gap report's — assistive only,
persisted on competency_gap, unable to affect the deterministic order.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.deps import get_llm_service
from app.errors import AppError
from app.main import app
from app.models import (
    Account,
    AccountRole,
    Assessment,
    AssessmentConcept,
    AssessmentSession,
    Attempt,
    CompetencyGap,
    Concept,
    ConceptDependency,
    Question,
    QuestionConcept,
    Role,
    UserProfile,
)
from app.security import hash_password
from app.services.guidance_service import session_study_guidance
from app.services.llm import LLMError


class StubLLM:
    """Canned gap_explain responses; records every prompt it receives."""

    def __init__(self, response=None, error=None):
        self.response = (
            {"explanation": "Practice the fundamentals first."}
            if response is None
            else response
        )
        self.error = error
        self.calls = []

    def generate_structured(
        self, task_type, messages, *, json_schema=None, max_tokens=None
    ):
        self.calls.append(
            {
                "task_type": task_type,
                "messages": list(messages),
                "json_schema": json_schema,
            }
        )
        if self.error is not None:
            raise self.error
        return self.response


# ---------- fixture helpers ----------


def _make_learner(db, email="learner@test.dev", name="Learner One"):
    account = Account(
        email=email, password_hash=hash_password("Secret123!"), status="active"
    )
    account.profile = UserProfile(full_name=name)
    role = db.query(Role).filter_by(role_name="Learner").one()
    db.add(account)
    db.flush()
    db.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
    db.commit()
    return account


def _make_concept(db, code, name=None, area="SQL Querying", description=None):
    concept = Concept(
        concept_code=code,
        concept_name=name or code,
        subject_area=area,
        description=description,
        difficulty_level=2,
    )
    db.add(concept)
    db.flush()
    return concept


def _make_session(db, learner, *, status="completed", targets=None):
    assessment = Assessment(
        title="Assessment", status="published", created_by=learner.account_id
    )
    db.add(assessment)
    db.flush()
    for concept, target in (targets or {}).items():
        db.add(
            AssessmentConcept(
                assessment_id=assessment.assessment_id,
                concept_id=concept.concept_id,
                target_pct=Decimal(str(target)),
            )
        )
    now = datetime.now(timezone.utc)
    session = AssessmentSession(
        assessment_id=assessment.assessment_id,
        learner_id=learner.account_id,
        status=status,
        expires_at=now + timedelta(minutes=60),
        submitted_at=now if status != "in_progress" else None,
    )
    db.add(session)
    db.flush()
    return session


def _add_question(db, creator_id, qtype="mcq", points="1.0", concept_ids=()):
    question = Question(
        question_type=qtype,
        prompt="prompt",
        points=Decimal(str(points)),
        status="validated",
        created_by=creator_id,
    )
    db.add(question)
    db.flush()
    for cid in concept_ids:
        db.add(
            QuestionConcept(
                question_id=question.question_id,
                concept_id=cid,
                confirmed=True,
            )
        )
    db.flush()
    return question


def _add_attempt(db, session, question, seq_no, score=None):
    attempt = Attempt(
        session_id=session.session_id,
        question_id=question.question_id,
        seq_no=seq_no,
        score=Decimal(str(score)) if score is not None else None,
        grading_detail={
            "grader": "answer_key",
            "question_type": question.question_type,
            "points_earned": str(score),
            "points_possible": str(question.points),
        },
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.flush()
    return attempt


def _edge(db, concept, prerequisite):
    """concept depends on prerequisite (prerequisite -> concept)."""
    db.add(
        ConceptDependency(
            concept_id=concept.concept_id,
            prerequisite_concept_id=prerequisite.concept_id,
        )
    )
    db.flush()


def _score_question(db, session, learner, concept, score, seq, points="4.0"):
    q = _add_question(
        db, learner.account_id, "mcq", points, [concept.concept_id]
    )
    return _add_attempt(db, session, q, seq, score=score)


# ---------- deterministic ordering ----------


class TestGuidanceOrdering:
    def test_no_gaps_empty_guidance(self, db_session):
        learner = _make_learner(db_session)
        c = _make_concept(db_session, "SQL-SELECT")
        session = _make_session(db_session, learner, targets={c: "50.0"})
        _score_question(db_session, session, learner, c, "4.00", 1)  # 100%
        db_session.commit()

        result = session_study_guidance(db_session, session.session_id, learner)
        assert result.guidance == []

    def test_single_gap(self, db_session):
        learner = _make_learner(db_session)
        c = _make_concept(db_session, "SQL-JOIN", name="Joins")
        session = _make_session(db_session, learner, targets={c: "75.0"})
        _score_question(db_session, session, learner, c, "2.00", 1)  # 50%
        db_session.commit()

        result = session_study_guidance(db_session, session.session_id, learner)
        assert len(result.guidance) == 1
        item = result.guidance[0]
        assert item.concept_id == c.concept_id
        assert item.priority == 1
        assert item.ready is True
        assert Decimal(item.shortfall) == Decimal("25.00")
        assert item.prerequisites == []

    def test_independent_gaps_ranked_by_shortfall(self, db_session):
        learner = _make_learner(db_session)
        small = _make_concept(db_session, "C-A", name="A")  # 80-50 = 30
        large = _make_concept(db_session, "C-B", name="B")  # 90-25 = 65
        session = _make_session(
            db_session, learner, targets={small: "80.0", large: "90.0"}
        )
        _score_question(db_session, session, learner, small, "2.00", 1)
        _score_question(db_session, session, learner, large, "1.00", 2)
        db_session.commit()

        result = session_study_guidance(db_session, session.session_id, learner)
        assert [g.concept_code for g in result.guidance] == ["C-B", "C-A"]
        assert [g.priority for g in result.guidance] == [1, 2]

    def test_prerequisite_gap_before_dependent_gap(self, db_session):
        """JOIN (gap 25) depends on SELECT (gap 10): SELECT is recommended
        first even though its shortfall is smaller."""
        learner = _make_learner(db_session)
        select_ = _make_concept(db_session, "SQL-SELECT", name="SELECT")
        join = _make_concept(db_session, "SQL-JOIN", name="Joins")
        _edge(db_session, join, select_)
        session = _make_session(
            db_session, learner, targets={select_: "60.0", join: "75.0"}
        )
        _score_question(db_session, session, learner, select_, "2.00", 1)  # 50%
        _score_question(db_session, session, learner, join, "2.00", 2)     # 50%
        db_session.commit()

        result = session_study_guidance(db_session, session.session_id, learner)
        assert [g.concept_code for g in result.guidance] == [
            "SQL-SELECT",
            "SQL-JOIN",
        ]
        join_item = result.guidance[1]
        assert join_item.ready is False
        assert join_item.prerequisites[0].concept_code == "SQL-SELECT"
        assert join_item.prerequisites[0].status == "below_target"
        assert "study prerequisite first" in join_item.reason
        assert "'SELECT'" in join_item.reason

    def test_multi_level_chain(self, db_session):
        learner = _make_learner(db_session)
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        c = _make_concept(db_session, "C-C")
        _edge(db_session, b, a)
        _edge(db_session, c, b)
        session = _make_session(
            db_session,
            learner,
            # C has the largest shortfall but sits at the top of the chain.
            targets={a: "60.0", b: "65.0", c: "95.0"},
        )
        _score_question(db_session, session, learner, a, "2.00", 1)  # 50%
        _score_question(db_session, session, learner, b, "2.00", 2)  # 50%
        _score_question(db_session, session, learner, c, "0.00", 3)  # 0%
        db_session.commit()

        result = session_study_guidance(db_session, session.session_id, learner)
        assert [g.concept_code for g in result.guidance] == ["C-A", "C-B", "C-C"]
        assert [g.ready for g in result.guidance] == [True, False, False]

    def test_multiple_prerequisites(self, db_session):
        learner = _make_learner(db_session)
        a = _make_concept(db_session, "C-A", name="A")
        b = _make_concept(db_session, "C-B", name="B")
        c = _make_concept(db_session, "C-C", name="C")
        _edge(db_session, c, a)
        _edge(db_session, c, b)
        session = _make_session(
            db_session,
            learner,
            targets={a: "60.0", b: "80.0", c: "90.0"},
        )
        _score_question(db_session, session, learner, a, "2.00", 1)  # 50%
        _score_question(db_session, session, learner, b, "2.00", 2)  # 50%
        _score_question(db_session, session, learner, c, "0.00", 3)  # 0%
        db_session.commit()

        result = session_study_guidance(db_session, session.session_id, learner)
        # B has the larger shortfall (30 vs 10) so it leads the ready pair.
        assert [g.concept_code for g in result.guidance] == [
            "C-B",
            "C-A",
            "C-C",
        ]
        c_item = result.guidance[2]
        assert [p.concept_code for p in c_item.prerequisites] == ["C-A", "C-B"]
        assert all(p.status == "below_target" for p in c_item.prerequisites)

    def test_satisfied_prerequisite_does_not_block(self, db_session):
        learner = _make_learner(db_session)
        ok = _make_concept(db_session, "SQL-WHERE", name="WHERE")
        weak = _make_concept(db_session, "SQL-JOIN", name="JOIN")
        _edge(db_session, weak, ok)
        session = _make_session(
            db_session, learner, targets={ok: "50.0", weak: "80.0"}
        )
        _score_question(db_session, session, learner, ok, "4.00", 1)   # 100%
        _score_question(db_session, session, learner, weak, "2.00", 2)  # 50%
        db_session.commit()

        result = session_study_guidance(db_session, session.session_id, learner)
        assert len(result.guidance) == 1
        item = result.guidance[0]
        assert item.concept_code == "SQL-JOIN"
        assert item.ready is True
        assert item.prerequisites[0].status == "satisfied"
        assert Decimal(item.prerequisites[0].competency_pct) == Decimal("100.00")

    def test_at_threshold_is_not_a_gap(self, db_session):
        """Exactly at benchmark => not a gap, never recommended, never a
        blocker for a dependent."""
        learner = _make_learner(db_session)
        at = _make_concept(db_session, "C-AT")
        dep = _make_concept(db_session, "C-DEP")
        _edge(db_session, dep, at)
        session = _make_session(
            db_session, learner, targets={at: "50.0", dep: "80.0"}
        )
        _score_question(db_session, session, learner, at, "2.00", 1)   # 50%
        _score_question(db_session, session, learner, dep, "0.00", 2)  # 0%
        db_session.commit()

        result = session_study_guidance(db_session, session.session_id, learner)
        assert [g.concept_code for g in result.guidance] == ["C-DEP"]
        assert result.guidance[0].ready is True
        assert result.guidance[0].prerequisites[0].status == "satisfied"

    def test_missing_evidence_is_not_a_gap(self, db_session):
        """A targeted but unassessed concept is not recommended — and as a
        prerequisite it reports 'unassessed' without blocking."""
        learner = _make_learner(db_session)
        unseen = _make_concept(db_session, "C-UNSEEN", name="Unseen")
        weak = _make_concept(db_session, "C-WEAK", name="Weak")
        _edge(db_session, weak, unseen)
        session = _make_session(
            db_session, learner, targets={unseen: "80.0", weak: "70.0"}
        )
        _score_question(db_session, session, learner, weak, "1.00", 1)  # 25%
        db_session.commit()

        result = session_study_guidance(db_session, session.session_id, learner)
        assert [g.concept_code for g in result.guidance] == ["C-WEAK"]
        item = result.guidance[0]
        assert item.ready is True
        prereq = item.prerequisites[0]
        assert prereq.concept_code == "C-UNSEEN"
        assert prereq.status == "unassessed"
        assert prereq.competency_pct is None
        assert Decimal(prereq.target_pct) == Decimal("80.00")
        assert "not yet assessed" in item.reason

    def test_no_graph_falls_back_to_shortfall_order(self, db_session):
        """With no concept_dependency rows at all, guidance equals the
        documented shortfall ranking."""
        learner = _make_learner(db_session)
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        session = _make_session(
            db_session, learner, targets={a: "90.0", b: "60.0"}
        )
        _score_question(db_session, session, learner, a, "2.00", 1)  # 50% gap 40
        _score_question(db_session, session, learner, b, "2.00", 2)  # 50% gap 10
        db_session.commit()

        result = session_study_guidance(db_session, session.session_id, learner)
        assert [g.concept_code for g in result.guidance] == ["C-A", "C-B"]

    def test_tie_breaks_on_concept_id(self, db_session):
        learner = _make_learner(db_session)
        c1 = _make_concept(db_session, "C-A")
        c2 = _make_concept(db_session, "C-B")
        session = _make_session(
            db_session, learner, targets={c1: "60.0", c2: "60.0"}
        )
        _score_question(db_session, session, learner, c2, "2.00", 1)
        _score_question(db_session, session, learner, c1, "2.00", 2)
        db_session.commit()

        result = session_study_guidance(db_session, session.session_id, learner)
        assert [g.concept_id for g in result.guidance] == sorted(
            [c1.concept_id, c2.concept_id]
        )

    def test_malformed_cycle_in_data_still_returns(self, db_session):
        """Cycle inserted outside the service (bad data) cannot hang the
        ordering — leftover concepts append deterministically."""
        learner = _make_learner(db_session)
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        _edge(db_session, b, a)
        _edge(db_session, a, b)  # a -> b -> a
        session = _make_session(
            db_session, learner, targets={a: "80.0", b: "60.0"}
        )
        _score_question(db_session, session, learner, a, "2.00", 1)
        _score_question(db_session, session, learner, b, "2.00", 2)
        db_session.commit()

        result = session_study_guidance(db_session, session.session_id, learner)
        assert [g.concept_id for g in result.guidance] == sorted(
            [a.concept_id, b.concept_id]
        )

    def test_idempotent_repeated_reads(self, db_session):
        learner = _make_learner(db_session)
        a = _make_concept(db_session, "C-A")
        b = _make_concept(db_session, "C-B")
        _edge(db_session, b, a)
        session = _make_session(
            db_session, learner, targets={a: "60.0", b: "80.0"}
        )
        _score_question(db_session, session, learner, a, "2.00", 1)
        _score_question(db_session, session, learner, b, "1.00", 2)
        db_session.commit()

        first = session_study_guidance(db_session, session.session_id, learner)
        second = session_study_guidance(db_session, session.session_id, learner)
        assert [g.model_dump() for g in first.guidance] == [
            g.model_dump() for g in second.guidance
        ]
        assert db_session.query(CompetencyGap).count() == 2  # no duplicates

    def test_traceability_fields(self, db_session):
        learner = _make_learner(db_session)
        c = _make_concept(
            db_session, "SQL-JOIN", name="Joins", description="multi-table"
        )
        session = _make_session(db_session, learner, targets={c: "80.0"})
        attempt = _score_question(db_session, session, learner, c, "2.00", 1)
        db_session.commit()

        item = session_study_guidance(
            db_session, session.session_id, learner
        ).guidance[0]
        assert item.contributing_attempts == [attempt.attempt_id]
        assert item.reason == "30.00 pts below the 80.00% benchmark"
        assert item.description == "multi-table"
        assert item.subject_area == "SQL Querying"


class TestGuidanceIsolation:
    def test_other_learner_404(self, db_session):
        owner = _make_learner(db_session, "owner@test.dev")
        other = _make_learner(db_session, "other@test.dev")
        session = _make_session(db_session, owner)
        db_session.commit()
        with pytest.raises(AppError) as exc:
            session_study_guidance(db_session, session.session_id, other)
        assert exc.value.status_code == 404

    def test_in_progress_conflicts(self, db_session):
        learner = _make_learner(db_session)
        session = _make_session(db_session, learner, status="in_progress")
        db_session.commit()
        with pytest.raises(AppError) as exc:
            session_study_guidance(db_session, session.session_id, learner)
        assert exc.value.status_code == 409
        assert exc.value.code == "session_not_finalized"


# ---------- LLM interaction (assistive only) ----------


@pytest.fixture()
def guidance_setup(db_session):
    learner = _make_learner(db_session)
    base = _make_concept(db_session, "SQL-SELECT", name="SELECT")
    dep = _make_concept(db_session, "SQL-JOIN", name="Joins")
    _edge(db_session, dep, base)
    session = _make_session(
        db_session, learner, targets={base: "60.0", dep: "90.0"}
    )
    _score_question(db_session, session, learner, base, "2.00", 1)  # gap 10
    _score_question(db_session, session, learner, dep, "0.00", 2)   # gap 90
    db_session.commit()
    return {"learner": learner, "session": session, "base": base, "dep": dep}


class TestGuidanceLLM:
    def test_explanation_attached_and_persisted(self, db_session, guidance_setup):
        stub = StubLLM()
        result = session_study_guidance(
            db_session,
            guidance_setup["session"].session_id,
            guidance_setup["learner"],
            stub,
        )
        assert all(
            g.llm_explanation == "Practice the fundamentals first."
            for g in result.guidance
        )
        assert {c["task_type"] for c in stub.calls} == {"gap_explain"}
        rows = db_session.query(CompetencyGap).all()
        assert all(r.llm_explanation for r in rows)

    def test_llm_cannot_affect_order(self, db_session, guidance_setup):
        """JOIN has the bigger shortfall but sits behind its gap prerequisite
        SELECT regardless of explanation content."""
        stub = StubLLM({"explanation": "STUDY JOINS FIRST!!!"})
        result = session_study_guidance(
            db_session,
            guidance_setup["session"].session_id,
            guidance_setup["learner"],
            stub,
        )
        assert [g.concept_code for g in result.guidance] == [
            "SQL-SELECT",
            "SQL-JOIN",
        ]

    def test_llm_unconfigured_still_guides(self, db_session, guidance_setup):
        stub = StubLLM(error=LLMError(LLMError.NOT_CONFIGURED, "no key"))
        result = session_study_guidance(
            db_session,
            guidance_setup["session"].session_id,
            guidance_setup["learner"],
            stub,
        )
        assert len(result.guidance) == 2
        assert all(g.llm_explanation is None for g in result.guidance)

    def test_llm_provider_failure_still_guides(
        self, db_session, guidance_setup
    ):
        stub = StubLLM(error=LLMError(LLMError.UNAVAILABLE, "down"))
        result = session_study_guidance(
            db_session,
            guidance_setup["session"].session_id,
            guidance_setup["learner"],
            stub,
        )
        assert [g.concept_code for g in result.guidance] == [
            "SQL-SELECT",
            "SQL-JOIN",
        ]

    def test_malformed_llm_response(self, db_session, guidance_setup):
        stub = StubLLM(response={"wrong": 1})
        result = session_study_guidance(
            db_session,
            guidance_setup["session"].session_id,
            guidance_setup["learner"],
            stub,
        )
        assert all(g.llm_explanation is None for g in result.guidance)

    def test_no_llm_argument_works(self, db_session, guidance_setup):
        result = session_study_guidance(
            db_session,
            guidance_setup["session"].session_id,
            guidance_setup["learner"],
        )
        assert len(result.guidance) == 2

    def test_explanations_cached_across_reads(self, db_session, guidance_setup):
        stub = StubLLM()
        sid = guidance_setup["session"].session_id
        learner = guidance_setup["learner"]
        session_study_guidance(db_session, sid, learner, stub)
        session_study_guidance(db_session, sid, learner, stub)
        assert len(stub.calls) == 2  # one call per gap, not per read


# ---------- endpoint ----------


def _login(client, email, password="Secret123!"):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]


@pytest.fixture()
def endpoint_setup(db_session, client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Learner One",
            "email": "learner@test.dev",
            "password": "Secret123!",
            "password_confirm": "Secret123!",
        },
    )
    token = _login(client, "learner@test.dev")
    learner = db_session.query(Account).filter_by(email="learner@test.dev").one()
    base = _make_concept(db_session, "SQL-SELECT", name="SELECT")
    dep = _make_concept(db_session, "SQL-JOIN", name="Joins")
    _edge(db_session, dep, base)
    session = _make_session(
        db_session, learner, targets={base: "60.0", dep: "80.0"}
    )
    _score_question(db_session, session, learner, base, "2.00", 1)
    _score_question(db_session, session, learner, dep, "0.00", 2)
    db_session.commit()
    return {"token": token, "session_id": session.session_id}


class TestGuidanceEndpoint:
    URL = "/api/v1/sessions/{}/guidance"

    def test_response_shape(self, client, endpoint_setup):
        r = client.get(
            self.URL.format(endpoint_setup["session_id"]),
            headers={"Authorization": f"Bearer {endpoint_setup['token']}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["session_id"] == endpoint_setup["session_id"]
        assert [g["concept_code"] for g in body["guidance"]] == [
            "SQL-SELECT",
            "SQL-JOIN",
        ]
        first, second = body["guidance"]
        assert first["priority"] == 1 and first["ready"] is True
        assert second["priority"] == 2 and second["ready"] is False
        assert second["prerequisites"][0]["status"] == "below_target"
        assert Decimal(second["shortfall"]) == Decimal("80.00")

    def test_idempotent_endpoint(self, client, endpoint_setup):
        headers = {"Authorization": f"Bearer {endpoint_setup['token']}"}
        url = self.URL.format(endpoint_setup["session_id"])
        a = client.get(url, headers=headers).json()
        b = client.get(url, headers=headers).json()
        assert a == b

    def test_unauthenticated(self, client, endpoint_setup):
        assert (
            client.get(self.URL.format(endpoint_setup["session_id"])).status_code
            == 401
        )

    def test_other_learner_404(self, client, endpoint_setup, db_session):
        _make_learner(db_session, "other@test.dev")
        db_session.commit()
        token = _login(client, "other@test.dev")
        r = client.get(
            self.URL.format(endpoint_setup["session_id"]),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404

    def test_admin_forbidden(self, client, endpoint_setup, db_session):
        admin = Account(
            email="admin@test.dev",
            password_hash=hash_password("Admin123!"),
            status="active",
        )
        admin.profile = UserProfile(full_name="A")
        role = db_session.query(Role).filter_by(role_name="Administrator").one()
        db_session.add(admin)
        db_session.flush()
        db_session.add(AccountRole(account_id=admin.account_id, role_id=role.role_id))
        db_session.commit()
        token = _login(client, "admin@test.dev", "Admin123!")
        r = client.get(
            self.URL.format(endpoint_setup["session_id"]),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403

    def test_llm_stub_via_dependency_override(
        self, client, endpoint_setup, db_session
    ):
        stub = StubLLM({"explanation": "Focus on SELECT basics."})
        app.dependency_overrides[get_llm_service] = lambda: stub
        try:
            r = client.get(
                self.URL.format(endpoint_setup["session_id"]),
                headers={"Authorization": f"Bearer {endpoint_setup['token']}"},
            )
        finally:
            app.dependency_overrides.pop(get_llm_service, None)
        assert r.status_code == 200
        assert all(
            g["llm_explanation"] == "Focus on SELECT basics."
            for g in r.json()["guidance"]
        )
