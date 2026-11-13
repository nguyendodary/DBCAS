"""Preview and start reject the same invalid bank candidates."""
from uuid import UUID

import pytest
from sqlalchemy import update

from app.models import AssessmentSession, McqOption
from app.services.practice_bank import preview_plan
from app.services.practice_service import PracticeStart
from test_learner_practice import fixture, selection
from test_supervisor_requirements import headers


@pytest.mark.parametrize("shuffle", [False, True])
def test_preview_and_start_skip_an_invalid_validated_bank_question(client, db_session, shuffle):
    _, learner, concepts = fixture(db_session, shuffle=shuffle)
    payload = selection(concepts[:1])
    payload["request_id"] = str(UUID(int=1))
    _, initial = preview_plan(db_session, learner, PracticeStart(**payload))
    invalid_id = next(pick.candidate.identity for pick in initial if pick.candidate.kind == "mcq")
    db_session.execute(update(McqOption).where(McqOption.question_id == invalid_id).values(is_correct=False))
    db_session.commit()
    db_session.expire_all()

    preview = client.post("/api/v1/practice/preview", headers=headers(learner), json=payload)
    assert preview.status_code == 200, preview.text
    _, preview_picks = preview_plan(db_session, learner, PracticeStart(**payload))
    preview_ids = [pick.candidate.identity for pick in preview_picks]
    started = client.post("/api/v1/practice/start", headers=headers(learner), json=payload)
    assert started.status_code == 200, started.text
    session = db_session.get(AssessmentSession, started.json()["session_id"])

    assert invalid_id not in preview_ids
    assert invalid_id not in session.config_snapshot["question_ids"]
    assert preview_ids == session.config_snapshot["question_ids"]
