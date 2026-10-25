from datetime import datetime, timezone, timedelta
from decimal import Decimal
from types import SimpleNamespace as Row

from app.services import analytics_service, evidence_context


def test_latest_graded_results_ties_and_unscored_learners(monkeypatch):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    sessions = [Row(session_id=i, learner_id=learner, assessment_id=assessment,
                    started_at=now + timedelta(days=i), submitted_at=None, status='completed', release_status='published')
                for i, learner, assessment in [(1, 1, 1), (2, 1, 1), (3, 1, 2),
                                                (4, 2, 1), (5, 1, 1), (6, 4, 1)]]
    # Old 100% is replaced by 80%; pending resit 5 cannot replace it.
    attempts = [Row(session_id=i, score=score, submitted_at=now, points=Decimal(10))
                for i, score in [(1, Decimal(10)), (2, Decimal(8)),
                                 (3, Decimal(6)), (4, Decimal(7)), (5, None), (6, Decimal(0))]]
    roster = [Row(account_id=i, email=f'{i}@example.test', full_name=f'Student {i}')
              for i in range(1, 5)]
    repo = Row(finalized_sessions=lambda scope: sessions,
               learner_accounts=lambda: roster)
    monkeypatch.setattr(analytics_service, 'AssessmentRepository',
                        lambda db: Row(history_attempts=lambda ids: attempts))
    monkeypatch.setattr(evidence_context, 'question_view', lambda attempt: attempt)
    rows = analytics_service.learner_leaderboard(None, repo, None)
    assert [(r.account_id, r.average_pct, r.rank, r.assessments_graded) for r in rows] == [
        (1, Decimal('70.00'), 1, 2), (2, Decimal('70.00'), 1, 1),
        (4, Decimal('0.00'), 3, 1), (3, None, None, 0),
    ]


def test_scope_and_unanswered_questions(monkeypatch):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    session = Row(session_id=1, learner_id=1, assessment_id=42, submitted_at=now, started_at=now, status='completed', release_status='published')
    seen = []
    def sessions(scope):
        seen.append(scope)
        return [session]
    repo = Row(finalized_sessions=sessions, learner_accounts=lambda: [
        Row(account_id=1, email='1@example.test', full_name=None)])
    attempts = [Row(session_id=1, score=Decimal(10), submitted_at=now, points=Decimal(10)),
                Row(session_id=1, score=None, submitted_at=None, points=Decimal(10))]
    monkeypatch.setattr(analytics_service, 'AssessmentRepository',
                        lambda db: Row(history_attempts=lambda ids: attempts))
    monkeypatch.setattr(evidence_context, 'question_view', lambda attempt: attempt)
    rows = analytics_service.learner_leaderboard(None, repo, 42)
    assert seen == [42]
    assert rows[0].average_pct == Decimal('50.00')


def test_empty_roster(monkeypatch):
    repo = Row(finalized_sessions=lambda scope: [], learner_accounts=lambda: [])
    monkeypatch.setattr(analytics_service, 'AssessmentRepository',
                        lambda db: Row(history_attempts=lambda ids: []))
    assert analytics_service.learner_leaderboard(None, repo, None) == []


def test_unpublished_results_cannot_contribute_to_student_ranking(monkeypatch):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    session = Row(session_id=1, learner_id=1, assessment_id=1, submitted_at=now, started_at=now,
                  status='completed', release_status='pending_review')
    repo = Row(finalized_sessions=lambda scope: [session], learner_accounts=lambda: [Row(account_id=1, full_name='Student', email='private@example.test')])
    seen = []
    def attempts(ids):
        seen.extend(ids)
        return []
    monkeypatch.setattr(analytics_service, 'AssessmentRepository', lambda _: Row(history_attempts=attempts))
    rows = analytics_service.learner_leaderboard(None, repo, None)
    assert seen == []
    assert rows[0].average_pct is None and rows[0].rank is None


def test_student_response_does_not_include_emails_or_administrator_data(monkeypatch):
    from app.schemas import LearnerRankingItem
    monkeypatch.setattr(analytics_service, 'AnalyticsRepository', lambda _: None)
    monkeypatch.setattr(analytics_service, 'learner_leaderboard', lambda *args: [LearnerRankingItem(
        account_id=1, email='private@example.test', full_name='Student', rank=1, average_pct=80, assessments_graded=2)])
    row = analytics_service.student_leaderboard(None)[0].model_dump()
    assert set(row) == {'account_id', 'full_name', 'rank', 'average_pct', 'assessments_graded'}
