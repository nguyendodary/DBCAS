"""Local optional AI must preserve submissions and allow instructor completion."""
import pytest
from sqlalchemy import select

from app.config import get_settings
from app.deps import get_llm_service
from app.main import app
from app.models import GradingJob
from app.services.llm import LLMService
from test_ai_admin import _make_account
from test_draft_lifecycle import _fixture, _essay_service
from test_supervisor_requirements import headers
from test_adaptive_engine import _mcq


def _essay_fixture(db, *, policy="IMMEDIATE"):
    fixture = _fixture(db, "essay", policy=policy)
    learner, _, _, _, concept, _, _ = fixture
    # The submit-and-advance endpoint requires a valid opening bank even when
    # a regression fixture starts from an already served essay.
    for index in range(3):
        _mcq(db, concept, diff=1, admin=learner, prompt=f"Opening item {index}")
    db.commit()
    return fixture


@pytest.mark.parametrize("policy", ["IMMEDIATE", "HUMAN_VERIFIED"])
def test_unconfigured_essay_can_be_reviewed_and_published_without_changing_policy(client, db_session, policy):
    learner, session, attempt, question, _, learner_headers, answer = _essay_fixture(db_session, policy=policy)
    admin = _make_account(db_session, "instructor@test.dev", "Administrator")
    disabled = LLMService(get_settings().model_copy(update={"llm_api_key": "", "llm_base_url": "", "llm_model": ""}))
    app.dependency_overrides[get_llm_service] = lambda: disabled
    try:
        response = client.post(f"/api/v1/sessions/{session.session_id}/submit",
                               headers=learner_headers, json={"question_id": question.question_id, **answer})
        assert response.status_code == 200 and response.json()["answer"]["score"] is None, response.json()
        finished = client.post(f"/api/v1/sessions/{session.session_id}/finish", headers=learner_headers)
        assert finished.json()["release_status"] == "pending_review"
        assert finished.json()["result_release_policy"] == policy
        queue = client.get('/api/v1/admin/grading-reviews', headers=headers(admin, "Administrator")).json()
        assert [row['session_id'] for row in queue] == [session.session_id]
        detail = client.get(f'/api/v1/admin/grading-reviews/{session.session_id}', headers=headers(admin, "Administrator")).json()
        assert detail['manual_review_required'] is True
        reviewed = client.post(f'/api/v1/admin/grading-reviews/{session.session_id}/attempts/{attempt.attempt_id}',
            headers=headers(admin, "Administrator"), json={"revision": 0, "score": "0.75", "comments": "Reviewed against rubric"})
        assert reviewed.status_code == 200, reviewed.json()
        if policy == 'HUMAN_VERIFIED':
            assert reviewed.json()['release_status'] == 'reviewed'
            published = client.post(f'/api/v1/admin/grading-reviews/{session.session_id}/publish',
                headers=headers(admin, "Administrator"), json={"revision": reviewed.json()['revision']})
            assert published.status_code == 200
        result = client.get(f'/api/v1/sessions/{session.session_id}/evidence', headers=learner_headers)
        assert result.status_code == 200 and result.json()['items'][0]['score'] == '0.75'
        db_session.refresh(attempt)
        assert attempt.essay_answer == answer['essay_answer'] and attempt.grading_status == 'graded'
        assert db_session.scalar(select(GradingJob)).status == 'completed'
    finally:
        app.dependency_overrides.pop(get_llm_service, None)


def test_configured_local_api_queues_essay_then_worker_grades_with_real_provider_adapter(client, db_session, monkeypatch):
    from app import worker
    _, session, attempt, question, _, learner_headers, answer = _essay_fixture(db_session)
    settings = get_settings()
    for key, value in {"auto_grade_essays": True, "llm_api_key": "test-only", "llm_base_url": "https://mock.test", "llm_model": "fixture"}.items():
        monkeypatch.setattr(settings, key, value)
    service = _essay_service(db_session)
    app.dependency_overrides[get_llm_service] = lambda: service
    try:
        response = client.post(f'/api/v1/sessions/{session.session_id}/submit', headers=learner_headers,
                               json={"question_id": question.question_id, **answer})
        assert response.status_code == 200 and response.json()['answer']['score'] is None, response.json()
        db_session.refresh(attempt)
        assert not attempt.grading_detail.get('awaiting_instructor')
        monkeypatch.setattr(worker, 'build_llm_service', lambda settings, db: _essay_service(db))
        worker.maintenance_tick()
        db_session.refresh(attempt)
        assert attempt.score == 1 and attempt.grading_status == 'graded'
        assert db_session.scalar(select(GradingJob)).status == 'completed'
    finally:
        app.dependency_overrides.pop(get_llm_service, None)


def test_timed_out_local_essay_draft_waits_for_instructor_without_provider(client, db_session, monkeypatch):
    from app.services.assessment_lifecycle import finalize
    _, session, attempt, _, _, _, answer = _fixture(db_session, 'essay', policy='HUMAN_VERIFIED')
    monkeypatch.setattr(get_settings(), 'auto_grade_essays', True)
    for key in ('llm_api_key', 'llm_base_url', 'llm_model'):
        monkeypatch.setattr(get_settings(), key, '')
    attempt.draft_answer = answer
    db_session.commit()
    finalize(db_session, session, timed_out=True)
    assert session.release_status == 'pending_review'
    assert attempt.essay_answer == answer['essay_answer']
