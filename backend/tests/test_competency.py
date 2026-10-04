"""Competency scoring engine tests — Task 4.1 (DBCAS-22 / FR-12).

The engine consumes the deterministic evidence Sprint 2–3 graders persist
(``attempt.score`` per graded answer); tests therefore write graded attempts
directly (the same contract the real graders produce) and additionally cover
one end-to-end MCQ submission → competency read.

Documented formula: ``competency_pct = points_earned / points_possible × 100``
per (session, concept); ``below_target = competency_pct < target_pct``.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.db import get_session_factory
from app.models import (
    Account,
    AccountRole,
    Assessment,
    AssessmentConcept,
    AssessmentSession,
    Attempt,
    Concept,
    ConceptCompetency,
    McqOption,
    Question,
    QuestionConcept,
    Role,
    UserProfile,
)
from app.security import hash_password
from app.services.competency_service import (
    compute_session_competency,
    session_competency_profile,
)
from app.errors import AppError


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


def _make_concept(
    db, code, name=None, area="SQL Querying", description=None, difficulty=2
):
    concept = Concept(
        concept_code=code,
        concept_name=name or code,
        subject_area=area,
        description=description,
        difficulty_level=difficulty,
    )
    db.add(concept)
    db.flush()
    return concept


def _make_session(db, learner, *, status="completed", targets=None):
    """A finalized (default) session; ``targets`` maps Concept -> target_pct."""
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
    finalized = status != "in_progress"
    session = AssessmentSession(
        assessment_id=assessment.assessment_id,
        learner_id=learner.account_id,
        status=status,
        expires_at=now + timedelta(minutes=60),
        submitted_at=now if finalized else None,
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


def _add_attempt(
    db, session, question, seq_no, score=None, submitted=True
):
    """A served attempt; ``submitted=True`` mirrors the graders' contract
    (deterministic score + grading_detail evidence + submitted_at)."""
    attempt = Attempt(
        session_id=session.session_id,
        question_id=question.question_id,
        seq_no=seq_no,
        score=Decimal(str(score)) if score is not None else None,
        grading_detail=(
            {
                "grader": "answer_key",
                "question_type": question.question_type,
                "points_earned": str(score),
                "points_possible": str(question.points),
            }
            if submitted
            else None
        ),
        submitted_at=datetime.now(timezone.utc) if submitted else None,
    )
    db.add(attempt)
    db.flush()
    return attempt


def _by_concept(rows):
    return {r.concept_id: r for r in rows}


# ---------- aggregation unit tests (service level) ----------


class TestCompetencyAggregation:
    def test_mcq_only_evidence(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-SELECT")
        session = _make_session(db_session, learner)
        q = _add_question(db_session, learner.account_id, "mcq", "2.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="2.00")
        db_session.commit()

        rows = compute_session_competency(db_session, session)
        row = rows[0]
        assert row.points_earned == Decimal("2.00")
        assert row.points_possible == Decimal("2.00")
        assert row.competency_pct == Decimal("100.00")

    def test_sql_only_evidence(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-JOIN")
        session = _make_session(db_session, learner)
        q = _add_question(db_session, learner.account_id, "sql", "5.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="2.50")
        db_session.commit()

        row = compute_session_competency(db_session, session)[0]
        assert row.points_earned == Decimal("2.50")
        assert row.points_possible == Decimal("5.00")
        assert row.competency_pct == Decimal("50.00")

    def test_essay_only_evidence(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "DB-NORM", area="Constraints & Design Fundamentals")
        session = _make_session(db_session, learner)
        q = _add_question(db_session, learner.account_id, "essay", "4.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="3.00")
        db_session.commit()

        row = compute_session_competency(db_session, session)[0]
        assert row.competency_pct == Decimal("75.00")

    def test_mixed_types_aggregate_by_points_not_type_weights(self, db_session):
        """MCQ+SQL+essay evidence adds raw points — there is no per-format
        weighting in the documented model (would give 60% at 20/50/30)."""
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-WHERE")
        session = _make_session(db_session, learner)
        q_mcq = _add_question(db_session, learner.account_id, "mcq", "2.0", [concept.concept_id])
        q_sql = _add_question(db_session, learner.account_id, "sql", "2.0", [concept.concept_id])
        q_essay = _add_question(db_session, learner.account_id, "essay", "2.0", [concept.concept_id])
        _add_attempt(db_session, session, q_mcq, 1, score="1.00")   # 50%
        _add_attempt(db_session, session, q_sql, 2, score="2.00")   # 100%
        _add_attempt(db_session, session, q_essay, 3, score="0.00") # 0%
        db_session.commit()

        row = compute_session_competency(db_session, session)[0]
        assert row.points_earned == Decimal("3.00")
        assert row.points_possible == Decimal("6.00")
        assert row.competency_pct == Decimal("50.00")

    def test_multiple_answers_one_concept(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-GROUPBY")
        session = _make_session(db_session, learner)
        q1 = _add_question(db_session, learner.account_id, "mcq", "2.0", [concept.concept_id])
        q2 = _add_question(db_session, learner.account_id, "mcq", "2.0", [concept.concept_id])
        _add_attempt(db_session, session, q1, 1, score="1.00")
        _add_attempt(db_session, session, q2, 2, score="2.00")
        db_session.commit()

        row = compute_session_competency(db_session, session)[0]
        assert row.points_earned == Decimal("3.00")
        assert row.points_possible == Decimal("4.00")
        assert row.competency_pct == Decimal("75.00")

    def test_one_question_contributes_to_each_tagged_concept(self, db_session):
        """Junction semantics: a question mapped to two concepts feeds both
        fully (question_concept defines no per-tag weight)."""
        learner = _make_learner(db_session)
        c1 = _make_concept(db_session, "SQL-JOIN")
        c2 = _make_concept(db_session, "SQL-WHERE")
        session = _make_session(db_session, learner)
        q = _add_question(
            db_session, learner.account_id, "sql", "4.0",
            [c1.concept_id, c2.concept_id],
        )
        _add_attempt(db_session, session, q, 1, score="3.00")
        db_session.commit()

        rows = _by_concept(compute_session_competency(db_session, session))
        assert rows[c1.concept_id].competency_pct == Decimal("75.00")
        assert rows[c2.concept_id].competency_pct == Decimal("75.00")
        assert rows[c1.concept_id].points_possible == Decimal("4.00")
        assert rows[c2.concept_id].points_possible == Decimal("4.00")

    def test_different_max_points_normalized_by_points(self, db_session):
        """Point-weighted normalization: 2/2 + 4/8 -> 60%, not the 75% a
        naive average of per-question ratios would produce."""
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-ORDER")
        session = _make_session(db_session, learner)
        q_small = _add_question(db_session, learner.account_id, "mcq", "2.0", [concept.concept_id])
        q_big = _add_question(db_session, learner.account_id, "sql", "8.0", [concept.concept_id])
        _add_attempt(db_session, session, q_small, 1, score="2.00")  # 100%
        _add_attempt(db_session, session, q_big, 2, score="4.00")    # 50%
        db_session.commit()

        row = compute_session_competency(db_session, session)[0]
        assert row.points_earned == Decimal("6.00")
        assert row.points_possible == Decimal("10.00")
        assert row.competency_pct == Decimal("60.00")

    def test_perfect_score(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-CTE")
        session = _make_session(db_session, learner)
        q = _add_question(db_session, learner.account_id, "sql", "3.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="3.00")
        db_session.commit()

        row = compute_session_competency(db_session, session)[0]
        assert row.competency_pct == Decimal("100.00")
        assert row.below_target is False

    def test_zero_score_still_counts_as_evidence(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-HAVING")
        session = _make_session(
            db_session, learner, targets={concept: "50.0"}
        )
        q = _add_question(db_session, learner.account_id, "mcq", "2.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="0.00")
        db_session.commit()

        row = compute_session_competency(db_session, session)[0]
        assert row.points_earned == Decimal("0.00")
        assert row.competency_pct == Decimal("0.00")
        assert row.below_target is True

    def test_unsubmitted_attempt_is_not_evidence(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-DISTINCT")
        session = _make_session(db_session, learner)
        q = _add_question(db_session, learner.account_id, "mcq", "2.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, submitted=False)  # served, never answered
        db_session.commit()

        assert compute_session_competency(db_session, session) == []

    def test_unsubmitted_attempt_excluded_from_possible(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-DISTINCT")
        session = _make_session(db_session, learner)
        q1 = _add_question(db_session, learner.account_id, "mcq", "2.0", [concept.concept_id])
        q2 = _add_question(db_session, learner.account_id, "mcq", "2.0", [concept.concept_id])
        _add_attempt(db_session, session, q1, 1, score="2.00")
        _add_attempt(db_session, session, q2, 2, submitted=False)
        db_session.commit()

        row = compute_session_competency(db_session, session)[0]
        assert row.points_possible == Decimal("2.00")
        assert row.competency_pct == Decimal("100.00")

    def test_question_without_concept_tag_contributes_nothing(self, db_session):
        learner = _make_learner(db_session)
        _make_concept(db_session, "SQL-VIEW")
        session = _make_session(db_session, learner)
        q = _add_question(db_session, learner.account_id, "mcq", "2.0", [])
        _add_attempt(db_session, session, q, 1, score="2.00")
        db_session.commit()

        assert compute_session_competency(db_session, session) == []

    def test_concepts_without_evidence_get_no_row(self, db_session):
        """Unassessed target concepts are not reported — missing evidence is
        not a zero."""
        learner = _make_learner(db_session)
        assessed = _make_concept(db_session, "SQL-SELECT")
        unassessed = _make_concept(db_session, "DDL-CREATE")
        session = _make_session(
            db_session, learner,
            targets={assessed: "60.0", unassessed: "60.0"},
        )
        q = _add_question(db_session, learner.account_id, "mcq", "1.0", [assessed.concept_id])
        _add_attempt(db_session, session, q, 1, score="1.00")
        db_session.commit()

        rows = compute_session_competency(db_session, session)
        assert [r.concept_id for r in rows] == [assessed.concept_id]

    def test_rounding_half_up(self, db_session):
        """1.00 / 160.00 = 0.625% -> 0.63 under ROUND_HALF_UP (banker's
        rounding would give 0.62)."""
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-WINDOW")
        session = _make_session(db_session, learner)
        q = _add_question(db_session, learner.account_id, "sql", "160.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="1.00")
        db_session.commit()

        row = compute_session_competency(db_session, session)[0]
        assert row.competency_pct == Decimal("0.63")

    def test_recompute_is_idempotent(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-SUBQUERY")
        session = _make_session(db_session, learner)
        q = _add_question(db_session, learner.account_id, "mcq", "4.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="2.00")
        db_session.commit()

        first = compute_session_competency(db_session, session)[0]
        first_id = first.competency_id
        second = compute_session_competency(db_session, session)[0]
        assert second.competency_id == first_id  # upsert, not a new row
        assert second.competency_pct == first.competency_pct
        total = db_session.query(ConceptCompetency).filter_by(
            session_id=session.session_id
        ).count()
        assert total == 1  # no duplicate records

    def test_stale_row_removed_when_evidence_disappears(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-SET-OP")
        orphan = _make_concept(db_session, "DDL-ALTER")
        session = _make_session(db_session, learner)
        db_session.add(
            ConceptCompetency(
                session_id=session.session_id,
                concept_id=orphan.concept_id,
                points_earned=Decimal("1.00"),
                points_possible=Decimal("1.00"),
                competency_pct=Decimal("100.00"),
            )
        )
        q = _add_question(db_session, learner.account_id, "mcq", "1.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="1.00")
        db_session.commit()

        rows = compute_session_competency(db_session, session)
        assert {r.concept_id for r in rows} == {concept.concept_id}

    def test_score_never_exceeds_scale(self, db_session):
        """Defensive clamp: malformed evidence pushing pct over 100 is capped."""
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-FK")
        session = _make_session(db_session, learner)
        q = _add_question(db_session, learner.account_id, "mcq", "1.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="5.00")  # corrupt evidence
        db_session.commit()

        row = compute_session_competency(db_session, session)[0]
        assert row.competency_pct == Decimal("100.00")


class TestBelowTargetFlag:
    """below_target = competency_pct < target_pct; only assessment targets
    carry a benchmark."""

    @pytest.mark.parametrize(
        "earned,possible,target,expected",
        [
            ("2.00", "4.00", "50.0", False),   # exactly at target -> not a gap
            ("1.99", "4.00", "50.0", True),    # just below
            ("2.01", "4.00", "50.0", False),   # just above
            ("4.00", "4.00", "100.0", False),  # perfect vs strictest target
            ("0.00", "4.00", "1.0", True),     # zero vs any positive target
        ],
    )
    def test_threshold_boundary(self, db_session, earned, possible, target, expected):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-NULL")
        session = _make_session(db_session, learner, targets={concept: target})
        q = _add_question(
            db_session, learner.account_id, "mcq", str(possible), [concept.concept_id]
        )
        _add_attempt(db_session, session, q, 1, score=earned)
        db_session.commit()

        row = compute_session_competency(db_session, session)[0]
        assert row.below_target is expected

    def test_non_target_concept_never_flagged(self, db_session):
        learner = _make_learner(db_session)
        concept = _make_concept(db_session, "SQL-UNION")
        session = _make_session(db_session, learner)  # no targets configured
        q = _add_question(db_session, learner.account_id, "mcq", "4.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="0.00")
        db_session.commit()

        row = compute_session_competency(db_session, session)[0]
        assert row.below_target is False

    def test_different_targets_per_concept(self, db_session):
        learner = _make_learner(db_session)
        strict = _make_concept(db_session, "SQL-JOIN")   # target 90
        lenient = _make_concept(db_session, "SQL-WHERE") # target 40
        session = _make_session(
            db_session, learner,
            targets={strict: "90.0", lenient: "40.0"},
        )
        q1 = _add_question(db_session, learner.account_id, "mcq", "2.0", [strict.concept_id])
        q2 = _add_question(db_session, learner.account_id, "mcq", "2.0", [lenient.concept_id])
        _add_attempt(db_session, session, q1, 1, score="1.00")  # 50% < 90
        _add_attempt(db_session, session, q2, 2, score="1.00")  # 50% >= 40
        db_session.commit()

        rows = _by_concept(compute_session_competency(db_session, session))
        assert rows[strict.concept_id].below_target is True
        assert rows[lenient.concept_id].below_target is False


class TestLearnerIsolation:
    def test_profile_rejects_other_learners_session(self, db_session):
        owner = _make_learner(db_session, "owner@test.dev")
        other = _make_learner(db_session, "other@test.dev")
        session = _make_session(db_session, owner)
        db_session.commit()

        with pytest.raises(AppError) as exc:
            session_competency_profile(db_session, session.session_id, other)
        assert exc.value.status_code == 404  # existence not leaked

    def test_profile_rejects_unknown_session(self, db_session):
        learner = _make_learner(db_session)
        with pytest.raises(AppError) as exc:
            session_competency_profile(db_session, 999999, learner)
        assert exc.value.status_code == 404

    def test_in_progress_session_conflicts(self, db_session):
        learner = _make_learner(db_session)
        session = _make_session(db_session, learner, status="in_progress")
        db_session.commit()

        with pytest.raises(AppError) as exc:
            session_competency_profile(db_session, session.session_id, learner)
        assert exc.value.status_code == 409
        assert exc.value.code == "session_not_finalized"

    def test_expired_session_is_finalized_then_computed(self, db_session):
        learner = _make_learner(db_session)
        session = _make_session(db_session, learner, status="in_progress")
        session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        concept = _make_concept(db_session, "SQL-SELECT")
        q = _add_question(db_session, learner.account_id, "mcq", "1.0", [concept.concept_id])
        _add_attempt(db_session, session, q, 1, score="1.00")
        db_session.commit()

        result = session_competency_profile(db_session, session.session_id, learner)
        assert result.status == "timed_out"
        assert result.concepts[0].competency_pct == Decimal("100.00")
        db_session.refresh(session)
        assert session.status == "timed_out"


# ---------- endpoint tests ----------


def _login(client, email, password="Secret123!"):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]


@pytest.fixture()
def finalized_session(db_session, client):
    """A completed session with one graded MCQ attempt on a targeted concept."""
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
    concept = _make_concept(db_session, "SQL-PK", name="Primary Keys")
    session = _make_session(
        db_session, learner, targets={concept: "60.0"}
    )
    question = _add_question(
        db_session, learner.account_id, "mcq", "2.0", [concept.concept_id]
    )
    attempt = _add_attempt(db_session, session, question, 1, score="1.00")
    db_session.commit()
    return {
        "token": token,
        "session_id": session.session_id,
        "concept_id": concept.concept_id,
        "attempt_id": attempt.attempt_id,
    }


class TestCompetencyEndpoint:
    URL = "/api/v1/sessions/{}/competency"

    def test_profile_response(self, client, finalized_session):
        r = client.get(
            self.URL.format(finalized_session["session_id"]),
            headers={"Authorization": f"Bearer {finalized_session['token']}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["session_id"] == finalized_session["session_id"]
        assert body["status"] == "completed"
        assert len(body["concepts"]) == 1
        item = body["concepts"][0]
        assert item["concept_id"] == finalized_session["concept_id"]
        assert item["concept_code"] == "SQL-PK"
        assert item["concept_name"] == "Primary Keys"
        assert Decimal(item["points_earned"]) == Decimal("1.00")
        assert Decimal(item["points_possible"]) == Decimal("2.00")
        assert Decimal(item["competency_pct"]) == Decimal("50.00")
        assert Decimal(item["target_pct"]) == Decimal("60.00")
        assert item["below_target"] is True
        assert item["contributing_attempts"] == [finalized_session["attempt_id"]]

    def test_row_persisted(self, client, finalized_session, db_session):
        client.get(
            self.URL.format(finalized_session["session_id"]),
            headers={"Authorization": f"Bearer {finalized_session['token']}"},
        )
        row = db_session.query(ConceptCompetency).filter_by(
            session_id=finalized_session["session_id"]
        ).one()
        assert row.competency_pct == Decimal("50.00")
        assert row.below_target is True

    def test_repeat_reads_do_not_duplicate(self, client, finalized_session, db_session):
        url = self.URL.format(finalized_session["session_id"])
        headers = {"Authorization": f"Bearer {finalized_session['token']}"}
        client.get(url, headers=headers)
        r = client.get(url, headers=headers)
        assert r.status_code == 200
        assert db_session.query(ConceptCompetency).filter_by(
            session_id=finalized_session["session_id"]
        ).count() == 1

    def test_unauthenticated(self, client, finalized_session):
        r = client.get(self.URL.format(finalized_session["session_id"]))
        assert r.status_code == 401

    def test_other_learner_404(self, client, finalized_session, db_session):
        _make_learner(db_session, "other@test.dev")
        db_session.commit()
        token = _login(client, "other@test.dev")
        r = client.get(
            self.URL.format(finalized_session["session_id"]),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404

    def test_admin_forbidden(self, client, finalized_session, db_session):
        admin = Account(
            email="admin@test.dev",
            password_hash=hash_password("Admin123!"),
            status="active",
        )
        admin.profile = UserProfile(full_name="A")
        role = db_session.query(Role).filter_by(role_name="Administrator").one()
        db_session.add(admin)
        db_session.flush()
        db_session.add(
            AccountRole(account_id=admin.account_id, role_id=role.role_id)
        )
        db_session.commit()
        token = _login(client, "admin@test.dev", "Admin123!")
        r = client.get(
            self.URL.format(finalized_session["session_id"]),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403


class TestEndToEndGradingPipeline:
    """Real MCQ grading -> persisted evidence -> competency profile."""

    def test_mcq_submission_flows_into_competency(self, client, db_session):
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "E2E",
                "email": "e2e@test.dev",
                "password": "Secret123!",
                "password_confirm": "Secret123!",
            },
        )
        token = _login(client, "e2e@test.dev")
        learner = db_session.query(Account).filter_by(email="e2e@test.dev").one()
        concept = _make_concept(db_session, "SQL-PK")
        assessment = Assessment(
            title="E2E", status="published", created_by=learner.account_id
        )
        db_session.add(assessment)
        db_session.flush()
        db_session.add(
            AssessmentConcept(
                assessment_id=assessment.assessment_id,
                concept_id=concept.concept_id,
                target_pct=Decimal("50.0"),
            )
        )
        session = AssessmentSession(
            assessment_id=assessment.assessment_id,
            learner_id=learner.account_id,
            status="in_progress",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
        )
        question = Question(
            question_type="mcq",
            prompt="Which key uniquely identifies a row?",
            points=Decimal("2.0"),
            status="validated",
            created_by=learner.account_id,
        )
        question.options = [
            McqOption(option_label="A", option_text="Foreign key", is_correct=False),
            McqOption(option_label="B", option_text="Primary key", is_correct=True),
        ]
        db_session.add_all([session, question])
        db_session.flush()
        db_session.add(
            QuestionConcept(
                question_id=question.question_id,
                concept_id=concept.concept_id,
                confirmed=True,
            )
        )
        attempt = Attempt(
            session_id=session.session_id,
            question_id=question.question_id,
            seq_no=1,
        )
        db_session.add(attempt)
        db_session.commit()

        # grade the real way — the answer key path
        r = client.post(
            f"/api/v1/sessions/{session.session_id}/answers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "question_id": question.question_id,
                "selected_option_id": next(
                    o.option_id for o in question.options if o.is_correct
                ),
            },
        )
        assert r.status_code == 200

        # session ends; profile becomes readable
        session.status = "completed"
        session.submitted_at = datetime.now(timezone.utc)
        db_session.commit()

        r = client.get(
            f"/api/v1/sessions/{session.session_id}/competency",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        item = r.json()["concepts"][0]
        assert Decimal(item["competency_pct"]) == Decimal("100.00")
        assert item["below_target"] is False
        assert item["contributing_attempts"] == [attempt.attempt_id]
