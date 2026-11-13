"""Coverage preview stays within the selected scope and matches the real start."""
from collections import Counter
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from app.models import AssessmentSession
from app.services.practice_bank import preview_plan
from app.services.practice_service import PracticeStart
from test_learner_practice import fixture, selection
from test_supervisor_requirements import headers


REQUEST_IDS = [UUID(int=number) for number in (1, 2, 3, 4, 5)] + [
    uuid5(NAMESPACE_URL, f"preview-scope-{number}") for number in range(1, 6)
]
SHUFFLED_REQUEST_IDS = [
    uuid5(NAMESPACE_URL, f"preview-shuffled-{number}") for number in range(1, 5)
]


def _assert_selected_scope_and_plan_parity(client, db_session, request_id, *, shuffle):
    _, learner, concepts = fixture(db_session, shuffle=shuffle)
    selected = {concepts[0].concept_id}
    payload = selection(concepts[:1])
    payload["request_id"] = str(request_id)

    preview = client.post("/api/v1/practice/preview", headers=headers(learner), json=payload)
    assert preview.status_code == 200, preview.text
    _, preview_picks = preview_plan(db_session, learner, PracticeStart(**payload))
    preview_ids = [pick.candidate.identity for pick in preview_picks]
    started = client.post("/api/v1/practice/start", headers=headers(learner), json=payload)
    assert started.status_code == 200, started.text

    body = preview.json()
    preview_covered = {item["concept_id"] for item in body["covered_concepts"]}
    preview_uncovered = {item["concept_id"] for item in body["uncovered_concepts"]}
    session = db_session.get(AssessmentSession, started.json()["session_id"])
    plan = session.config_snapshot["question_plan"]
    start_covered = {item["concept_id"] for question in plan for item in question["concepts"]} & selected
    start_uncovered = {item["concept_id"] for item in started.json()["uncovered_concepts"]}

    assert start_covered | start_uncovered == selected
    assert preview_covered | preview_uncovered == selected, (
        f"preview covered={preview_covered}, uncovered={preview_uncovered}; "
        f"start covered={start_covered}, uncovered={start_uncovered}; shuffle={shuffle}"
    )
    assert preview_covered == start_covered
    assert preview_uncovered == start_uncovered
    assert preview_ids == session.config_snapshot["question_ids"]
    assert body["question_count"] == len(session.config_snapshot["question_ids"])
    assert body["type_counts"] == dict(Counter(question["question_type"] for question in plan))


@pytest.mark.parametrize("request_id", REQUEST_IDS)
def test_preview_and_start_disclose_only_selected_concepts(client, db_session, request_id):
    _assert_selected_scope_and_plan_parity(client, db_session, request_id, shuffle=False)


@pytest.mark.parametrize("request_id", SHUFFLED_REQUEST_IDS)
def test_preview_parity_does_not_depend_on_question_insertion_order(client, db_session, request_id):
    _assert_selected_scope_and_plan_parity(client, db_session, request_id, shuffle=True)
