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
