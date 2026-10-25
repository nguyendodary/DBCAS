"""Server-owned history, display aggregation and analytics regressions."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models import Attempt
from app.services.competency_service import profile_for_session
from app.services.session_service import sessions_for_learner_id
from app.services.analytics_service import cohort_overview, list_learners
from app.services.evidence_context import capture_assessment, capture_question
from app.repositories import AssessmentRepository
from test_competency import _make_learner, _make_concept, _make_session, _add_question, _add_attempt


def _results(db):
    learner = _make_learner(db)
    c1 = _make_concept(db, "TARGET", name="Target concept")
    c2 = _make_concept(db, "OTHER", name="Without benchmark")
    session = _make_session(db, learner, targets={c1: 60})
    q1 = _add_question(db, learner.account_id, points=2, concept_ids=[c1.concept_id])
    q2 = _add_question(db, learner.account_id, points=6, concept_ids=[c2.concept_id])
    _add_attempt(db, session, q1, 1, score=2)
    _add_attempt(db, session, q2, 2, score=0)
    db.commit()
    return learner, session, c1, c2, q1, q2


def test_unbenchmarked_concepts_are_not_meeting_target(db_session):
    learner, session, *_ = _results(db_session)
    profile = profile_for_session(db_session, session)
    assert profile.summary.model_dump() == dict(assessed_concepts=2, benchmarked_concepts=1,
        meeting_target=1, unbenchmarked_concepts=1, finalized_assessments=1)
    assert profile.categories[0].mean_competency_pct == Decimal("50.00")
    assert profile.categories[0].mean_target_pct == Decimal("60.00")


def test_unbenchmarked_category_has_null_target(db_session):
    _, session, _, c2, *_ = _results(db_session)
    c2.subject_area = "Separate category"
    db_session.commit()
    category = next(c for c in profile_for_session(db_session, session).categories if c.subject_area == "Separate category")
    assert category.mean_target_pct is None
    assert category.benchmarked_concepts == 0


def test_history_uses_weighted_answer_result_and_concept_results(db_session):
    learner, session, *_ = _results(db_session)
    result = sessions_for_learner_id(db_session, learner.account_id)[0]
    assert result.overall_result_pct == Decimal("25.00")  # 2/8, never average concept scores
    assert [c.competency_pct for c in result.concepts] == [Decimal("100.00"), Decimal("0.00")]
    assert result.graded_count == 2


def test_pending_grade_is_not_a_final_overall_score(db_session):
    learner, session, *_ = _results(db_session)
    attempt = db_session.query(Attempt).filter_by(session_id=session.session_id, seq_no=2).one()
    attempt.score = None
    attempt.grading_status = "pending"
    db_session.commit()
    result = sessions_for_learner_id(db_session, learner.account_id)[0]
    assert result.overall_result_pct is None
    assert result.pending_grading_count == 1
    assert len(result.concepts) == 1
    trend = cohort_overview(db_session, None).trend[0]
    assert trend.finalized_sessions == 1
    assert trend.graded_sessions == 0
    assert trend.mean_result_pct is None


def test_repeat_profile_read_does_not_rewrite_computed_timestamp(db_session):
    _, session, *_ = _results(db_session)
    first = profile_for_session(db_session, session)
    from app.models import ConceptCompetency
    before = {r.concept_id: r.computed_at for r in db_session.query(ConceptCompetency).all()}
    assert profile_for_session(db_session, session) == first
    assert before == {r.concept_id: r.computed_at for r in db_session.query(ConceptCompetency).all()}


def test_latest_history_orders_by_finalization_not_start(db_session):
    learner, first, *_ = _results(db_session)
    second = _make_session(db_session, learner, status="timed_out")
    now = datetime.now(timezone.utc)
    first.started_at = now - timedelta(days=2)
    first.submitted_at = now
    second.started_at = now - timedelta(days=1)
    second.submitted_at = now - timedelta(hours=1)
    db_session.commit()
    assert [s.session_id for s in sessions_for_learner_id(db_session, learner.account_id)] == [first.session_id, second.session_id]


def test_history_and_non_target_metadata_survive_edits(db_session):
    learner, session, c1, c2, q1, q2 = _results(db_session)
    session.config_snapshot = capture_assessment(session.assessment)
    repo = AssessmentRepository(db_session)
    for attempt in db_session.query(Attempt).all():
        attempt.question_snapshot = capture_question(repo, attempt.question)
    db_session.commit()
    before = sessions_for_learner_id(db_session, learner.account_id)[0]
    session.assessment.title = "Changed title"
    c2.concept_name = "Changed non-target concept"
    q1.points = Decimal("100")
    q2.points = Decimal("100")
    db_session.commit()
    after = sessions_for_learner_id(db_session, learner.account_id)[0]
    assert after == before
    assert profile_for_session(db_session, session).concepts[1].concept_name == "Without benchmark"


def test_analytics_trend_and_roster_activity_use_real_results(db_session):
    learner, session, *_ = _results(db_session)
    learner.status = "disabled"
    newer = _make_session(db_session, learner, status="in_progress")
    now = datetime.now(timezone.utc)
    newer.started_at = now + timedelta(minutes=1)
    db_session.commit()
    overview = cohort_overview(db_session, session.assessment_id)
    assert overview.trend[0].mean_result_pct == Decimal("25.00")
    assert overview.trend[0].graded_sessions == 1
    roster = list_learners(db_session)[0]
    assert roster.status == "disabled"
    assert roster.last_activity == newer.started_at
