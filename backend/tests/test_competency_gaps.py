"""Skill-gap detection tests — Task 4.2 (DBCAS-23 / FR-14, UC17).

A competency gap = a concept whose competency_pct is strictly below the
assessment's administrator-set target_pct. The ordered report is the
documented "What to study next" list (largest shortfall first). LLM
explanations are assistive-only: cached, optional, and structurally unable
to change scores or order.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.deps import get_llm_service
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
    Question,
    QuestionConcept,
    Role,
    UserProfile,
)
from app.security import hash_password
from app.services.competency_service import (
    detect_session_gaps,
    session_gap_report,
)
from app.services.llm import LLMError
from app.errors import AppError


class StubLLM:
    """Canned gap_explain responses; records the prompts it was given."""

    def __init__(self, response=None, error=None):
        self.response = (
            {"explanation": "Review JOIN syntax and practice multi-table queries."}
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


def _add_attempt(db, session, question, seq_no, score=None, detail=None):
    attempt = Attempt(
        session_id=session.session_id,
        question_id=question.question_id,
        seq_no=seq_no,
        score=Decimal(str(score)) if score is not None else None,
        grading_detail=detail
        or {
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


# ---------- deterministic detection ----------


class TestGapDetection:
    def test_below_threshold_creates_gap(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-JOIN", name="Joins")
        session = _make_session(db_session, learner, targets={concept: "70.0"})
        q = _add_question(db_session, learner.account_id, "mcq", "4.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="2.00")  # 50% < 70
        db_session.commit()

        gaps = detect_session_gaps(db_session, session)
        assert len(gaps) == 1
        assert gaps[0].concept_id == concept.concept_id
        assert gaps[0].status == "open"
        assert gaps[0].llm_explanation is None

    def test_at_threshold_is_not_a_gap(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-WHERE")
        session = _make_session(db_session, learner, targets={concept: "50.0"})
        q = _add_question(db_session, learner.account_id, "mcq", "4.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="2.00")  # exactly 50%
        db_session.commit()

        assert detect_session_gaps(db_session, session) == []

    def test_above_threshold_no_gap(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-SELECT")
        session = _make_session(db_session, learner, targets={concept: "50.0"})
        q = _add_question(db_session, learner.account_id, "mcq", "4.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="3.00")  # 75% > 50
        db_session.commit()

        assert detect_session_gaps(db_session, session) == []

    def test_zero_competency_gaps_at_full_shortfall(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-HAVING")
        session = _make_session(db_session, learner, targets={concept: "60.0"})
        q = _add_question(db_session, learner.account_id, "sql", "5.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="0.00")
        db_session.commit()

        report = session_gap_report(db_session, session.session_id, learner)
        assert len(report.gaps) == 1
        assert Decimal(report.gaps[0].competency_pct) == Decimal("0.00")
        assert Decimal(report.gaps[0].gap) == Decimal("60.00")  # 60 - 0

    def test_no_evidence_never_gaps(self, db_session):
        """A targeted but unassessed concept is not a gap — missing evidence
        is distinct from a low measured competency."""
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "DDL-CREATE")
        session = _make_session(db_session, learner, targets={concept: "80.0"})
        db_session.commit()

        assert detect_session_gaps(db_session, session) == []
        assert session_gap_report(
            db_session, session.session_id, learner
        ).gaps == []

    def test_multiple_concepts_mixed(self, db_session):
        learner = _make_learner(db_session)
        weak = _make_concept(db_session, "SQL-JOIN")
        ok = _make_concept(db_session, "SQL-WHERE")
        untouched = _make_concept(db_session, "SQL-CTE")  # no assessment target
        session = _make_session(
            db_session, learner, targets={weak: "70.0", ok: "40.0"}
        )
        q1 = _add_question(db_session, learner.account_id, "mcq", "4.0", [weak.concept_id])
        q2 = _add_question(db_session, learner.account_id, "mcq", "4.0", [ok.concept_id])
        q3 = _add_question(db_session, learner.account_id, "mcq", "4.0", [untouched.concept_id])
        _add_attempt(db_session, session, q1, 1, score="1.00")  # 25% < 70 -> gap
        _add_attempt(db_session, session, q2, 2, score="3.00")  # 75% >= 40 -> ok
        _add_attempt(db_session, session, q3, 3, score="0.00")  # 0%, no target
        db_session.commit()

        gaps = detect_session_gaps(db_session, session)
        assert [g.concept_id for g in gaps] == [weak.concept_id]

    def test_same_pct_different_targets(self, db_session):
        learner = _make_learner(db_session)
        strict = _make_concept(db_session, "SQL-WINDOW")
        lenient = _make_concept(db_session, "SQL-DISTINCT")
        session = _make_session(
            db_session, learner,
            targets={strict: "60.0", lenient: "40.0"},
        )
        for i, concept in enumerate((strict, lenient)):
            q = _add_question(
                db_session, learner.account_id, "mcq", "4.0", [concept.concept_id]
            )
            _add_attempt(db_session, session, q, i + 1, score="2.00")  # both 50%
        db_session.commit()

        gaps = detect_session_gaps(db_session, session)
        assert [g.concept_id for g in gaps] == [strict.concept_id]

    def test_ranked_by_shortfall_descending(self, db_session):
        learner = _make_learner(db_session)
        small = _make_concept(db_session, "SQL-A", name="A")    # 80-50 = 30
        large = _make_concept(db_session, "SQL-B", name="B")    # 90-25 = 65
        session = _make_session(
            db_session, learner, targets={small: "80.0", large: "90.0"}
        )
        qa = _add_question(db_session, learner.account_id, "mcq", "4.0", [small.concept_id])
        qb = _add_question(db_session, learner.account_id, "mcq", "4.0", [large.concept_id])
        _add_attempt(db_session, session, qa, 1, score="2.00")  # 50%
        _add_attempt(db_session, session, qb, 2, score="1.00")  # 25%
        db_session.commit()

        report = session_gap_report(db_session, session.session_id, learner)
        assert [g.concept_code for g in report.gaps] == ["SQL-B", "SQL-A"]
        assert Decimal(report.gaps[0].gap) == Decimal("65.00")
        assert Decimal(report.gaps[1].gap) == Decimal("30.00")

    def test_tie_breaks_on_concept_id(self, db_session):
        learner = _make_learner(db_session)
        c1 = _make_concept(db_session, "C-A")
        c2 = _make_concept(db_session, "C-B")
        session = _make_session(
            db_session, learner, targets={c1: "60.0", c2: "60.0"}
        )
        for i, c in enumerate((c2, c1)):  # insert B first; ids still order
            q = _add_question(db_session, learner.account_id, "mcq", "4.0", [c.concept_id])
            _add_attempt(db_session, session, q, i + 1, score="2.00")  # 50% both
        db_session.commit()

        report = session_gap_report(db_session, session.session_id, learner)
        assert [g.concept_id for g in report.gaps] == sorted(
            [c1.concept_id, c2.concept_id]
        )

    def test_recompute_no_duplicates(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-JOIN")
        session = _make_session(db_session, learner, targets={concept: "70.0"})
        q = _add_question(db_session, learner.account_id, "mcq", "4.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="1.00")
        db_session.commit()

        first = detect_session_gaps(db_session, session)
        second = detect_session_gaps(db_session, session)
        assert [g.gap_id for g in first] == [g.gap_id for g in second]
        assert db_session.query(CompetencyGap).filter_by(
            session_id=session.session_id
        ).count() == 1

    def test_gap_resolved_after_competency_improves(self, db_session):
        """Re-graded evidence lifting a concept above target removes the gap."""
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-GROUPBY")
        session = _make_session(db_session, learner, targets={concept: "70.0"})
        q = _add_question(db_session, learner.account_id, "mcq", "4.0", [concept.concept_id])
        attempt = _add_attempt(db_session, session, q, 1, score="1.00")  # 25%
        db_session.commit()
        assert len(detect_session_gaps(db_session, session)) == 1

        attempt.score = Decimal("4.00")  # re-graded -> 100% >= 70
        db_session.commit()
        assert detect_session_gaps(db_session, session) == []
        assert db_session.query(CompetencyGap).count() == 0

    def test_reviewed_status_and_explanation_survive_recompute(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-SUBQUERY")
        session = _make_session(db_session, learner, targets={concept: "70.0"})
        q = _add_question(db_session, learner.account_id, "mcq", "4.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="1.00")
        db_session.commit()

        gap = detect_session_gaps(db_session, session)[0]
        gap.status = "reviewed"
        gap.llm_explanation = "Prior explanation"
        db_session.commit()

        again = detect_session_gaps(db_session, session)[0]
        assert again.gap_id == gap.gap_id
        assert again.status == "reviewed"
        assert again.llm_explanation == "Prior explanation"


class TestGapReportIsolation:
    def test_other_learner_404(self, db_session):
        owner = _make_learner(db_session, "owner@test.dev")
        other = _make_learner(db_session, "other@test.dev")
        session = _make_session(db_session, owner)
        db_session.commit()

        with pytest.raises(AppError) as exc:
            session_gap_report(db_session, session.session_id, other)
        assert exc.value.status_code == 404

    def test_in_progress_conflicts(self, db_session):
        learner = _make_learner(db_session)
        session = _make_session(db_session, learner, status="in_progress")
        db_session.commit()

        with pytest.raises(AppError) as exc:
            session_gap_report(db_session, session.session_id, learner)
        assert exc.value.status_code == 409
        assert exc.value.code == "session_not_finalized"


# ---------- LLM explanations (assistive only) ----------


@pytest.fixture()
def gap_setup(db_session):
    """Session with one below-target SQL concept ready for explanation."""
    learner = _make_learner(db_session)
    concept = _make_concept(
        db_session, "SQL-JOIN", name="Joins",
        description="Combine rows from multiple tables",
    )
    session = _make_session(db_session, learner, targets={concept: "80.0"})
    q = _add_question(db_session, learner.account_id, "sql", "5.0", [concept.concept_id])
    _add_attempt(
        db_session, session, q, 1, score="1.00",
        detail={
            "grader": "sql_semantic",
            "question_type": "sql",
            "status": "partial",
            "datasets_passed": 1,
            "datasets_total": 4,
            "missing_required_concepts": ["JOIN"],
            "points_earned": "1.00",
            "points_possible": "5.00",
        },
    )
    db_session.commit()
    return {"learner": learner, "session": session, "concept": concept}


class TestGapExplanations:
    def test_explanation_generated_and_persisted(self, db_session, gap_setup):
        stub = StubLLM()
        report = session_gap_report(
            db_session, gap_setup["session"].session_id, gap_setup["learner"], stub
        )
        item = report.gaps[0]
        assert item.llm_explanation.startswith("Review JOIN")
        assert stub.calls[0]["task_type"] == "gap_explain"
        assert stub.calls[0]["json_schema"]["name"] == "gap_explanation"

        gap_row = db_session.query(CompetencyGap).filter_by(
            session_id=gap_setup["session"].session_id
        ).one()
        assert gap_row.llm_explanation == item.llm_explanation

    def test_prompt_links_evidence_without_pii_or_answers(
        self, db_session, gap_setup
    ):
        stub = StubLLM()
        session_gap_report(
            db_session, gap_setup["session"].session_id, gap_setup["learner"], stub
        )
        prompt = stub.calls[0]["messages"][1].content
        assert "Joins" in prompt                     # concept name
        assert "80" in prompt and "20" in prompt     # target and competency
        assert "1/4 test datasets" in prompt         # grading outcome evidence
        assert "JOIN" in prompt                      # missing technique
        # never learner identity or hidden grading data
        assert "learner@test.dev" not in prompt
        assert "Learner One" not in prompt
        assert "expected_result" not in prompt
        assert "setup_sql" not in prompt

    def test_explanation_cached_via_stored_row(self, db_session, gap_setup):
        stub = StubLLM()
        sid, learner = gap_setup["session"].session_id, gap_setup["learner"]
        session_gap_report(db_session, sid, learner, stub)
        session_gap_report(db_session, sid, learner, stub)
        assert len(stub.calls) == 1  # second read reuses persisted explanation

    def test_unconfigured_llm_still_returns_gaps(self, db_session, gap_setup):
        stub = StubLLM(error=LLMError(LLMError.NOT_CONFIGURED, "no key"))
        report = session_gap_report(
            db_session, gap_setup["session"].session_id, gap_setup["learner"], stub
        )
        assert len(report.gaps) == 1
        assert report.gaps[0].llm_explanation is None

    def test_malformed_llm_output_leaves_null(self, db_session, gap_setup):
        stub = StubLLM(response={"unexpected": True})
        report = session_gap_report(
            db_session, gap_setup["session"].session_id, gap_setup["learner"], stub
        )
        assert report.gaps[0].llm_explanation is None
        gap_row = db_session.query(CompetencyGap).one()
        assert gap_row.llm_explanation is None

    def test_explanation_never_changes_order_or_score(
        self, db_session, gap_setup
    ):
        """The LLM payload cannot influence ranking — order is fixed before
        explanations attach."""
        learner = gap_setup["learner"]
        session = gap_setup["session"]
        second = _make_concept(db_session, "SQL-CTE", name="CTEs")
        db_session.add(
            AssessmentConcept(
                assessment_id=session.assessment_id,
                concept_id=second.concept_id,
                target_pct=Decimal("90.0"),
            )
        )
        q = _add_question(db_session, learner.account_id, "mcq", "4.0", [second.concept_id])
        _add_attempt(db_session, session, q, 2, score="0.00")  # 0% -> gap 90
        db_session.commit()

        stub = StubLLM()
        report = session_gap_report(db_session, session.session_id, learner, stub)
        # 90-point shortfall still ranks first regardless of explanation text
        assert [g.concept_code for g in report.gaps] == ["SQL-CTE", "SQL-JOIN"]
        assert len(stub.calls) == 2  # one explanation per gap


# ---------- endpoint tests ----------


def _login(client, email, password="Secret123!"):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]


@pytest.fixture()
def gap_endpoint_setup(db_session, client):
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
    concept = _make_concept(
        db_session, "SQL-NORM", name="Normalization",
        area="Constraints & Design Fundamentals",
        description="Design schemas free of redundancy",
    )
    session = _make_session(db_session, learner, targets={concept: "75.0"})
    q = _add_question(db_session, learner.account_id, "essay", "4.0", [concept.concept_id])
    _add_attempt(
        db_session, session, q, 1, score="2.00",
        detail={
            "grader": "llm_rubric",
            "question_type": "essay",
            "rubric_level": "Partial",
            "missing_concepts": ["transitive dependency"],
            "points_earned": "2.00",
            "points_possible": "4.00",
        },
    )
    db_session.commit()
    return {
        "token": token,
        "session_id": session.session_id,
        "concept_id": concept.concept_id,
    }


@pytest.fixture()
def stub_llm():
    stub = StubLLM({"explanation": "Work on transitive dependencies in 3NF."})
    app.dependency_overrides[get_llm_service] = lambda: stub
    yield stub
    app.dependency_overrides.pop(get_llm_service, None)


class TestGapEndpoint:
    URL = "/api/v1/sessions/{}/gaps"

    def test_report_response(self, client, gap_endpoint_setup, stub_llm):
        r = client.get(
            self.URL.format(gap_endpoint_setup["session_id"]),
            headers={"Authorization": f"Bearer {gap_endpoint_setup['token']}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["session_id"] == gap_endpoint_setup["session_id"]
        assert len(body["gaps"]) == 1
        item = body["gaps"][0]
        assert item["concept_code"] == "SQL-NORM"
        assert item["concept_name"] == "Normalization"
        assert item["description"] == "Design schemas free of redundancy"
        assert Decimal(item["competency_pct"]) == Decimal("50.00")
        assert Decimal(item["target_pct"]) == Decimal("75.00")
        assert Decimal(item["gap"]) == Decimal("25.00")
        assert item["status"] == "open"
        assert item["llm_explanation"] == "Work on transitive dependencies in 3NF."

    def test_gap_row_persisted(self, client, gap_endpoint_setup, stub_llm, db_session):
        client.get(
            self.URL.format(gap_endpoint_setup["session_id"]),
            headers={"Authorization": f"Bearer {gap_endpoint_setup['token']}"},
        )
        row = db_session.query(CompetencyGap).filter_by(
            session_id=gap_endpoint_setup["session_id"]
        ).one()
        assert row.status == "open"
        assert row.llm_explanation == "Work on transitive dependencies in 3NF."

    def test_unauthenticated(self, client, gap_endpoint_setup):
        assert client.get(self.URL.format(gap_endpoint_setup["session_id"])).status_code == 401

    def test_other_learner_404(self, client, gap_endpoint_setup, db_session):
        _make_learner(db_session, "other@test.dev")
        db_session.commit()
        token = _login(client, "other@test.dev")
        r = client.get(
            self.URL.format(gap_endpoint_setup["session_id"]),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404

    def test_admin_forbidden(self, client, gap_endpoint_setup, db_session):
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
            self.URL.format(gap_endpoint_setup["session_id"]),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403
