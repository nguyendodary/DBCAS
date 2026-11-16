"""Automatic CLO tagging tests. No provider or network call is made."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import (
    Account,
    CloConcept,
    Concept,
    CourseLearningOutcome,
    Question,
    QuestionClo,
    QuestionConcept,
)
from app.security import hash_password
from app.services.clo_tagging import (
    coverage_report,
    reachable_clos,
    tag_question,
    tag_unmapped_questions,
)
from app.services.llm import LLMError


class StubLLM:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def generate_structured(self, task_type, messages, **kwargs):
        self.calls.append(
            {
                "task_type": task_type,
                "messages": messages,
                "kwargs": kwargs,
            }
        )
        if self.error is not None:
            raise self.error
        return self.response


def _account(db, email="admin@clo.test"):
    account = Account(
        email=email,
        password_hash=hash_password("Secret123!"),
        status="active",
    )
    db.add(account)
    db.commit()
    return account


def _clo(db, account, code, title=None):
    clo = CourseLearningOutcome(
        clo_code=code,
        title=title or code,
        description=f"Outcome {code}",
        created_by=account.account_id,
    )
    db.add(clo)
    db.commit()
    return clo


def _concept(db, code, description=None):
    concept = Concept(
        concept_code=code,
        concept_name=f"Concept {code}",
        subject_area="SQL Querying",
        difficulty_level=2,
        description=description or f"Description {code}",
        keywords=["select"],
        learning_objectives=["write queries"],
    )
    db.add(concept)
    db.commit()
    return concept


def _question(db, account, prompt="A safe question"):
    question = Question(
        question_type="mcq",
        prompt=prompt,
        reference_answer="A safe answer",
        difficulty_level=1,
        points=Decimal("1.0"),
        source="bank",
        status="validated",
        created_by=account.account_id,
    )
    db.add(question)
    db.commit()
    return question


def _link_clo(db, clo, concept):
    db.add(
        CloConcept(
            clo_id=clo.clo_id,
            concept_id=concept.concept_id,
            mapping_source="admin",
            status="confirmed",
        )
    )


def _tag_concept(db, question, concept):
    db.add(
        QuestionConcept(
            question_id=question.question_id,
            concept_id=concept.concept_id,
            tag_source="admin",
            confirmed=True,
        )
    )


def _proposal(primary, secondary=()):
    return {
        "primary_clo_id": primary,
        "secondary_clo_ids": list(secondary),
        "rationale": "The outcomes match the concept metadata.",
    }


def test_single_reachable_clo_gets_direct_auto_assignment(db_session):
    admin = _account(db_session)
    clo = _clo(db_session, admin, "CLO-ONE")
    concept = _concept(db_session, "C-ONE")
    _link_clo(db_session, clo, concept)
    question = _question(db_session, admin)
    _tag_concept(db_session, question, concept)
    db_session.commit()

    llm = StubLLM(response=_proposal(clo.clo_id))
    result = tag_question(db_session, question.question_id, llm)

    assert result.outcome == "auto_assigned"
    assert result.primary_clo_id == clo.clo_id
    assert llm.calls == []
    row = db_session.get(QuestionClo, (question.question_id, clo.clo_id))
    assert row is not None
    assert row.is_primary is True
    assert row.status == "confirmed"
    assert row.tag_source == "auto"
    assert row.confirmed_at is not None


def test_ambiguous_question_gets_pending_ai_proposal(db_session):
    admin = _account(db_session)
    clo1 = _clo(db_session, admin, "CLO-A")
    clo2 = _clo(db_session, admin, "CLO-B")
    concept = _concept(db_session, "C-AMBIGUOUS")
    _link_clo(db_session, clo1, concept)
    _link_clo(db_session, clo2, concept)
    question = _question(db_session, admin)
    _tag_concept(db_session, question, concept)
    db_session.commit()

    llm = StubLLM(response=_proposal(clo1.clo_id, [clo2.clo_id]))
    result = tag_question(db_session, question.question_id, llm)

    assert result.outcome == "ai_proposed"
    assert result.primary_clo_id == clo1.clo_id
    assert result.secondary_clo_ids == (clo2.clo_id,)
    assert [call["task_type"] for call in llm.calls] == ["question_clo_tag"]
    rows = list(
        db_session.scalars(
            select(QuestionClo)
            .where(QuestionClo.question_id == question.question_id)
            .order_by(QuestionClo.clo_id)
        )
    )
    assert len(rows) == 2
    primary = next(row for row in rows if row.is_primary)
    secondary = next(row for row in rows if not row.is_primary)
    assert (primary.clo_id, primary.status, primary.tag_source, primary.confirmed_at) == (
        clo1.clo_id,
        "pending",
        "ai",
        None,
    )
    assert (secondary.clo_id, secondary.status, secondary.tag_source) == (
        clo2.clo_id,
        "pending",
        "ai",
    )


def test_zero_reachable_clos_uses_full_active_catalogue(db_session):
    admin = _account(db_session)
    clo = _clo(db_session, admin, "CLO-ONLY")
    concept = _concept(db_session, "C-UNMAPPED")
    question = _question(db_session, admin)
    _tag_concept(db_session, question, concept)
    db_session.commit()

    llm = StubLLM(response=_proposal(clo.clo_id))
    result = tag_question(db_session, question.question_id, llm)

    assert reachable_clos(db_session, question.question_id) == []
    assert result.outcome == "ai_proposed"
    assert result.primary_clo_id == clo.clo_id
    row = db_session.get(QuestionClo, (question.question_id, clo.clo_id))
    assert row is not None
    assert row.is_primary is True
    assert row.status == "pending"
    assert row.tag_source == "ai"


def test_invalid_ai_output_is_rejected(db_session):
    admin = _account(db_session)
    clo = _clo(db_session, admin, "CLO-INVALID")
    decoy = _clo(db_session, admin, "CLO-INVALID-2")
    concept = _concept(db_session, "C-INVALID")
    _link_clo(db_session, clo, concept)
    _link_clo(db_session, decoy, concept)
    question = _question(db_session, admin)
    _tag_concept(db_session, question, concept)
    db_session.commit()

    llm = StubLLM(
        response={
            "primary_clo_id": clo.clo_id,
            "secondary_clo_ids": "not-a-list",
            "rationale": "invalid",
        }
    )
    result = tag_question(db_session, question.question_id, llm)

    assert result.outcome == "failed"
    assert result.failure_code == LLMError.INVALID_RESPONSE
    assert result.reason_code == "secondary_clo_ids"
    assert db_session.scalar(
        select(QuestionClo.question_id).where(
            QuestionClo.question_id == question.question_id
        )
    ) is None


def test_ai_clo_outside_allowed_set_is_rejected(db_session):
    admin = _account(db_session)
    clo = _clo(db_session, admin, "CLO-ALLOWED")
    decoy = _clo(db_session, admin, "CLO-ALLOWED-2")
    other = _clo(db_session, admin, "CLO-OTHER")
    concept = _concept(db_session, "C-SCOPE")
    _link_clo(db_session, clo, concept)
    _link_clo(db_session, decoy, concept)
    question = _question(db_session, admin)
    _tag_concept(db_session, question, concept)
    db_session.commit()

    llm = StubLLM(response=_proposal(other.clo_id))
    result = tag_question(db_session, question.question_id, llm)

    assert result.outcome == "failed"
    assert result.failure_code == LLMError.INVALID_RESPONSE
    assert result.reason_code == "primary_clo_id"
    assert db_session.scalar(
        select(QuestionClo.question_id).where(
            QuestionClo.question_id == question.question_id
        )
    ) is None


def test_primary_must_not_repeat_as_secondary(db_session):
    admin = _account(db_session)
    clo = _clo(db_session, admin, "CLO-DUP")
    decoy = _clo(db_session, admin, "CLO-DUP-2")
    concept = _concept(db_session, "C-DUP")
    _link_clo(db_session, clo, concept)
    _link_clo(db_session, decoy, concept)
    question = _question(db_session, admin)
    _tag_concept(db_session, question, concept)
    db_session.commit()

    llm = StubLLM(response=_proposal(clo.clo_id, [clo.clo_id]))
    result = tag_question(db_session, question.question_id, llm)

    assert result.outcome == "failed"
    assert result.reason_code == "secondary_clo_ids"


def test_database_enforces_one_active_primary(db_session):
    admin = _account(db_session)
    clo1 = _clo(db_session, admin, "CLO-P1")
    clo2 = _clo(db_session, admin, "CLO-P2")
    question = _question(db_session, admin)
    db_session.add(
        QuestionClo(
            question_id=question.question_id,
            clo_id=clo1.clo_id,
            is_primary=True,
            status="confirmed",
            tag_source="admin",
            confirmed_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()
    db_session.add(
        QuestionClo(
            question_id=question.question_id,
            clo_id=clo2.clo_id,
            is_primary=True,
            status="pending",
            tag_source="ai",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    assert db_session.scalar(
        select(QuestionClo.question_id).where(
            QuestionClo.question_id == question.question_id
        )
    ) == question.question_id
    assert len(
        db_session.execute(
            select(QuestionClo).where(
                QuestionClo.question_id == question.question_id
            )
        ).scalars().all()
    ) == 1


def test_admin_tag_is_never_overwritten(db_session):
    admin = _account(db_session)
    auto_clo = _clo(db_session, admin, "CLO-AUTO")
    admin_clo = _clo(db_session, admin, "CLO-ADMIN")
    concept = _concept(db_session, "C-ADMIN")
    _link_clo(db_session, auto_clo, concept)
    question = _question(db_session, admin)
    _tag_concept(db_session, question, concept)
    db_session.add(
        QuestionClo(
            question_id=question.question_id,
            clo_id=admin_clo.clo_id,
            is_primary=True,
            status="confirmed",
            tag_source="admin",
            confirmed_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    llm = StubLLM(response=_proposal(auto_clo.clo_id))
    result = tag_question(db_session, question.question_id, llm)

    assert result.outcome == "skipped_existing"
    assert llm.calls == []
    rows = list(
        db_session.scalars(
            select(QuestionClo).where(
                QuestionClo.question_id == question.question_id
            )
        )
    )
    assert len(rows) == 1
    assert rows[0].clo_id == admin_clo.clo_id
    assert rows[0].tag_source == "admin"
    assert rows[0].status == "confirmed"


def test_repeated_tagging_is_idempotent(db_session):
    admin = _account(db_session)
    clo1 = _clo(db_session, admin, "CLO-I1")
    clo2 = _clo(db_session, admin, "CLO-I2")
    concept = _concept(db_session, "C-IDEMPOTENT")
    _link_clo(db_session, clo1, concept)
    _link_clo(db_session, clo2, concept)
    question = _question(db_session, admin)
    _tag_concept(db_session, question, concept)
    db_session.commit()

    llm = StubLLM(response=_proposal(clo1.clo_id, [clo2.clo_id]))
    first = tag_unmapped_questions(db_session, llm)
    assert first.processed == 1
    assert first.ai_proposed == 1
    snapshot = list(
        db_session.scalars(
            select(QuestionClo)
            .where(QuestionClo.question_id == question.question_id)
            .order_by(QuestionClo.clo_id)
        )
    )

    second = tag_unmapped_questions(db_session, llm)
    assert second.processed == 0
    assert len(llm.calls) == 1
    assert list(
        db_session.scalars(
            select(QuestionClo)
            .where(QuestionClo.question_id == question.question_id)
            .order_by(QuestionClo.clo_id)
        )
    ) == snapshot
    assert tag_question(db_session, question.question_id, llm).outcome == "skipped_existing"


def test_provider_unavailability_leaves_question_untagged_and_reports(db_session):
    admin = _account(db_session)
    clo = _clo(db_session, admin, "CLO-DOWN")
    decoy = _clo(db_session, admin, "CLO-DOWN-2")
    concept = _concept(db_session, "C-DOWN")
    _link_clo(db_session, clo, concept)
    _link_clo(db_session, decoy, concept)
    question = _question(db_session, admin)
    _tag_concept(db_session, question, concept)
    db_session.commit()

    llm = StubLLM(error=LLMError(LLMError.UNAVAILABLE, "provider down"))
    report = tag_unmapped_questions(db_session, llm)

    assert report.processed == 1
    assert report.failed == 1
    assert report.failures[0].question_id == question.question_id
    assert report.failures[0].failure_code == LLMError.UNAVAILABLE
    assert db_session.scalar(
        select(QuestionClo.question_id).where(
            QuestionClo.question_id == question.question_id
        )
    ) is None
    coverage = coverage_report(db_session)
    assert coverage.question_ids_without_primary == (question.question_id,)


def test_run_assigns_single_and_proposes_ambiguous_questions(db_session):
    admin = _account(db_session)
    direct = _clo(db_session, admin, "CLO-DIRECT")
    ambiguous1 = _clo(db_session, admin, "CLO-AMB1")
    ambiguous2 = _clo(db_session, admin, "CLO-AMB2")
    single_concept = _concept(db_session, "C-DIRECT")
    ambiguous_concept = _concept(db_session, "C-AMB")
    _link_clo(db_session, direct, single_concept)
    _link_clo(db_session, ambiguous1, ambiguous_concept)
    _link_clo(db_session, ambiguous2, ambiguous_concept)
    first = _question(db_session, admin, prompt="first question")
    second = _question(db_session, admin, prompt="second question")
    _tag_concept(db_session, first, single_concept)
    _tag_concept(db_session, second, ambiguous_concept)
    db_session.commit()

    llm = StubLLM(response=_proposal(ambiguous1.clo_id))
    report = tag_unmapped_questions(db_session, llm)

    assert report.processed == 2
    assert report.auto_assigned == 1
    assert report.ai_proposed == 1
    assert report.failed == 0
    coverage = coverage_report(db_session)
    assert coverage.questions_without_primary == 0
    assert coverage.counts_by_source == {"admin": 0, "auto": 1, "ai": 1}


def test_coverage_report_counts_and_unresolved_ids(db_session):
    admin = _account(db_session)
    clo = _clo(db_session, admin, "CLO-COVER")
    secondary_clo = _clo(db_session, admin, "CLO-COVER-2")
    covered = _question(db_session, admin, prompt="covered")
    proposed = _question(db_session, admin, prompt="proposed")
    missing = _question(db_session, admin, prompt="missing")
    rejected = _question(db_session, admin, prompt="rejected")
    db_session.add_all(
        [
            QuestionClo(
                question_id=covered.question_id,
                clo_id=clo.clo_id,
                is_primary=True,
                status="confirmed",
                tag_source="auto",
                confirmed_at=datetime.now(timezone.utc),
            ),
            QuestionClo(
                question_id=proposed.question_id,
                clo_id=clo.clo_id,
                is_primary=True,
                status="pending",
                tag_source="ai",
            ),
            QuestionClo(
                question_id=proposed.question_id,
                clo_id=secondary_clo.clo_id,
                is_primary=False,
                status="pending",
                tag_source="ai",
            ),
            QuestionClo(
                question_id=rejected.question_id,
                clo_id=clo.clo_id,
                is_primary=True,
                status="rejected",
                tag_source="admin",
            ),
        ]
    )
    db_session.commit()

    report = coverage_report(db_session)

    assert report.total_questions == 4
    assert report.counts_by_status == {"pending": 2, "confirmed": 1, "rejected": 1}
    assert report.counts_by_source == {"admin": 1, "auto": 1, "ai": 2}
    assert report.questions_without_primary == 2
    assert report.question_ids_without_primary == (
        missing.question_id,
        rejected.question_id,
    )
    assert report.questions_without_confirmed_primary == 3
    assert report.question_ids_without_confirmed_primary == (
        proposed.question_id,
        missing.question_id,
        rejected.question_id,
    )
    assert "prompt" not in report.as_dict()
    assert all(isinstance(value, int) for value in report.question_ids_without_primary)


def test_prompt_excludes_question_text_and_is_bounded(db_session):
    admin = _account(db_session)
    clo = _clo(db_session, admin, "CLO-SAFE")
    decoy = _clo(db_session, admin, "CLO-SAFE-2")
    concept = _concept(db_session, "C-SAFE", description="D" * 5000)
    _link_clo(db_session, clo, concept)
    _link_clo(db_session, decoy, concept)
    prompt_secret = "PROMPT_SECRET_SHOULD_NOT_LEAVE"
    answer_secret = "ANSWER_SECRET_SHOULD_NOT_LEAVE"
    question = _question(db_session, admin, prompt=prompt_secret)
    question.reference_answer = answer_secret
    _tag_concept(db_session, question, concept)
    db_session.commit()

    llm = StubLLM(response=_proposal(clo.clo_id))
    result = tag_question(db_session, question.question_id, llm)

    assert result.outcome == "ai_proposed"
    wire = "\n".join(message.content for message in llm.calls[0]["messages"])
    assert prompt_secret not in wire
    assert answer_secret not in wire
    assert "C-SAFE" in wire
    assert "CLO-SAFE" in wire
    assert len(wire) < 10000


def test_no_active_clo_fails_without_calling_provider(db_session):
    admin = _account(db_session)
    concept = _concept(db_session, "C-NONE")
    question = _question(db_session, admin)
    _tag_concept(db_session, question, concept)
    db_session.commit()

    llm = StubLLM(response={})
    result = tag_question(db_session, question.question_id, llm)

    assert result.outcome == "failed"
    assert result.failure_code == "no_allowed_clos"
    assert llm.calls == []
