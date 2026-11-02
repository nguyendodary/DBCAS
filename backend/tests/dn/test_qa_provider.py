"""The deterministic browser harness returns valid structured grades over HTTP."""
from http.server import ThreadingHTTPServer
import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from qa_provider import Handler, STATE, LOCK, RELEASE


@pytest.fixture
def provider_server():
    with LOCK:
        STATE.update(delay_seconds=0, failure=False, hold=False, calls=0)
        RELEASE.set()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def post(base, path, body):
    with urlopen(Request(base + path, json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=2) as response:
        return json.load(response)


def test_local_provider_returns_a_valid_band_despite_rubric_punctuation(provider_server):
    body = {"response_format": {"json_schema": {"name": "essay_grade"}}, "messages": [{"role": "user", "content":
        "- Complete: score 3.75 to 5.00. Criteria: valid dependencies\n\n"
        "STUDENT ANSWER (identifiers redacted):\nEach key determines its attributes.\n\nReturn JSON: {}"}]}
    response = post(provider_server, "/v1/chat/completions", body)
    grade = json.loads(response["choices"][0]["message"]["content"])
    assert grade["score"] == 4.38 and grade["rubric_level"] == "Complete"
    assert grade["evidence"] == ["Each key determines its attributes."]
    assert len(grade["matched_criteria"]) == len(grade["evidence"])


def test_local_provider_control_is_bounded_and_outages_use_http_errors(provider_server):
    with pytest.raises(HTTPError) as invalid:
        post(provider_server, "/control", {"delay_seconds": 121})
    assert invalid.value.code == 400
    held = post(provider_server, "/control", {"delay_seconds": 0, "hold": True})
    assert held["hold"] is True and not RELEASE.is_set()
    state = post(provider_server, "/control", {"delay_seconds": 0, "failure": True})
    assert state["failure"] is True and RELEASE.is_set()
    with pytest.raises(HTTPError) as outage:
        post(provider_server, "/v1/chat/completions", {
            "response_format": {"json_schema": {"name": "essay_grade"}},
            "messages": [{"role": "user", "content": "- Complete: score 3.75 to 5.00. Criteria: dependencies\n\n"
                "STUDENT ANSWER (identifiers redacted):\nA key determines its attributes.\n\nReturn JSON: {}"}],
        })
    assert outage.value.code == 503
    with pytest.raises(HTTPError) as unsupported:
        post(provider_server, "/v1/chat/completions", {"response_format": {"json_schema": {"name": "question_generation"}}})
    assert unsupported.value.code == 503


def test_local_provider_evaluation_obeys_the_prompt_schema(provider_server):
    from app.services.prompt_builder import template_prompt
    from app.services.evaluation_pipeline import validate_evaluation
    data = {"mode": "attempt", "attempt_count": 1, "items": [
        {"attempt_id": 1, "question_id": 2, "type": "mcq", "points": "1", "score": "1"}]}
    response = post(provider_server, "/v1/chat/completions", {
        "response_format": {"json_schema": {"name": "evaluation"}},
        "messages": [{"role": "user", "content": template_prompt(data)}],
    })
    result = validate_evaluation(json.loads(response["choices"][0]["message"]["content"]), data)
    assert result["trend"] is None
    assert result["question_comments"][0]["essay_score_proposal"] is None


def test_local_provider_generation_preserves_the_requested_scope(provider_server):
    from types import SimpleNamespace
    from uuid import uuid4
    from app.services.practice_service import PracticeStart, validate_generated
    scope = {"concepts": [{"id": 3, "name": "Khóa chính", "description": "Xác định duy nhất mỗi bản ghi."}],
             "difficulty_levels": [4, 5], "count": 3}
    response = post(provider_server, "/v1/chat/completions", {
        "response_format": {"json_schema": {"name": "practice_questions"}},
        "messages": [{"role": "user", "content": "Generate within this scope:\n" + json.dumps(scope)}],
    })
    raw = json.loads(response["choices"][0]["message"]["content"])
    request = PracticeStart(concept_ids=[3], difficulties=["HARD"], source="ai", question_count=3, request_id=uuid4())
    questions = validate_generated(raw, [SimpleNamespace(concept_id=3)], request, None)
    assert len(questions) == 3
    assert all(q["concept_ids"] == [3] and q["difficulty_level"] in {4, 5} for q in questions)
    assert all(sum(o["correct"] for o in q["options"]) == 1 for q in questions)
