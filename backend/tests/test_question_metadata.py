"""Seeded PostgreSQL metadata survives ordinary admin API edits."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from app.benchmark import import_pack
from app.config import ROOT_DIR, get_settings
from app.models import Assessment, AssessmentSession, Attempt, Question
from app.repositories import AssessmentRepository
from app.services.evidence_context import capture_assessment, capture_question
from app.services.sandbox_runner import SandboxRunner
from test_admin_questions import _make_account, _login

BASE = "/api/v1/admin/questions"


@pytest.fixture
def seeded_question(client, db_session):
    admin = _make_account(db_session, "metadata@test.dev", "Administrator")
    pack = json.loads((ROOT_DIR / "db/postgres_knowledge_pack.json").read_text(encoding="utf-8"))
    item = next(q for q in pack["questions"] if q["key"] == "pg-m089")
    pack["questions"] = [item]
    pack["concepts"] = [c for c in pack["concepts"] if c["concept_code"] in item["concept_codes"]]
    pack["clos"], pack["dependencies"], pack["assessments"] = [], {}, []
    imported = import_pack(db_session, admin, SandboxRunner(get_settings()), pack)
    headers = {"Authorization": f"Bearer {_login(client, admin.email)}"}
    qid = imported["question_ids"][0]
    before = client.get(f"{BASE}/{qid}", headers=headers).json()
    assert "postgres" in before["tags"]
    assert before["source_refs"] and all(
        ref["url"].startswith("https://www.postgresql.org/docs/18/")
        and ref["version"] and ref["section"] for ref in before["source_refs"])
    return admin, headers, before


def edit_payload(before):
    payload = deepcopy(before)
    payload["concept_ids"] = [c["concept_id"] for c in before["concepts"] if c["confirmed"]]
    payload["required_concept_ids"] = [c["concept_id"] for c in before["concepts"] if c["confirmed"] and c["is_required"]]
    payload["difficulty_level"] = 3
    return payload


@pytest.mark.parametrize("referenced", [False, True])
def test_omitted_metadata_survives_seeded_admin_edit(client, db_session, seeded_question, referenced):
    admin, headers, before = seeded_question
    qid = before["question_id"]
    old_translation = deepcopy(before["translations"])
    if referenced:
        assessment = Assessment(title="Metadata history", status="published", created_by=admin.account_id)
        db_session.add(assessment); db_session.flush()
        config = capture_assessment(assessment)
        session = AssessmentSession(assessment_id=assessment.assessment_id, learner_id=admin.account_id,
            status="completed", expires_at=datetime.now(timezone.utc), config_snapshot=config)
        db_session.add(session); db_session.flush()
        snapshot = capture_question(AssessmentRepository(db_session), db_session.get(Question, qid))
        attempt = Attempt(session_id=session.session_id, question_id=qid, seq_no=1,
                          question_snapshot=snapshot, score=1)
        db_session.add(attempt); db_session.commit()
    payload = edit_payload(before)
    payload.pop("tags")
    payload.pop("source_refs")
    response = client.put(f"{BASE}/{qid}", json=payload, headers=headers)
    assert response.status_code == 200, response.json()
    after = response.json()
    assert after["tags"] == before["tags"]
    assert after["source_refs"] == before["source_refs"]
    assert after["translations"] == old_translation
    assert after["status"] == "draft"
    assert after["version_no"] == before["version_no"] + int(referenced)
    assert (after["question_id"] != qid) == referenced
    found = client.get(BASE, params={"tag": "postgres", "q": before["prompt"]}, headers=headers).json()
    assert after["question_id"] in [q["question_id"] for q in found]
    if referenced:
        db_session.refresh(attempt); db_session.refresh(session)
        assert attempt.question_snapshot == snapshot and attempt.score == 1
        assert session.config_snapshot == config
        original = client.get(f"{BASE}/{qid}", headers=headers).json()
        assert original["tags"] == before["tags"] and original["source_refs"] == before["source_refs"]
        assert original["translations"] == old_translation and original["status"] == "retired"


@pytest.mark.parametrize("clear", [False, True])
def test_explicit_metadata_replaces_or_clears(client, seeded_question, clear):
    _, headers, before = seeded_question
    payload = edit_payload(before)
    payload["tags"] = [] if clear else ["postgres", "reviewed"]
    payload["source_refs"] = [] if clear else [before["source_refs"][0]]
    response = client.put(f"{BASE}/{before['question_id']}", json=payload, headers=headers)
    assert response.status_code == 200, response.json()
    after = response.json()
    assert after["tags"] == payload["tags"]
    assert after["source_refs"] == payload["source_refs"]


def test_create_without_metadata_still_defaults_empty(client, seeded_question):
    _, headers, before = seeded_question
    payload = edit_payload(before)
    payload.pop("tags"); payload.pop("source_refs")
    response = client.post(BASE, json=payload, headers=headers)
    assert response.status_code == 201, response.json()
    assert response.json()["tags"] == [] and response.json()["source_refs"] == []


@pytest.mark.parametrize("field", ["tags", "source_refs"])
def test_metadata_fields_are_independent(client, seeded_question, field):
    _, headers, before = seeded_question
    payload = edit_payload(before)
    other = "source_refs" if field == "tags" else "tags"
    payload.pop(other)
    payload[field] = []
    response = client.put(f"{BASE}/{before['question_id']}", json=payload, headers=headers)
    assert response.status_code == 200, response.json()
    assert response.json()[field] == []
    assert response.json()[other] == before[other]


@pytest.mark.parametrize("field", ["tags", "source_refs"])
def test_null_metadata_is_rejected_without_changes(client, seeded_question, field):
    _, headers, before = seeded_question
    payload = edit_payload(before)
    payload[field] = None
    assert client.put(f"{BASE}/{before['question_id']}", json=payload, headers=headers).status_code == 422
    assert client.get(f"{BASE}/{before['question_id']}", headers=headers).json() == before


def test_retired_edit_preserves_metadata_and_lifecycle(client, seeded_question):
    _, headers, before = seeded_question
    qid = before["question_id"]
    assert client.patch(f"{BASE}/{qid}", json={"status": "retired"}, headers=headers).status_code == 200
    payload = edit_payload(before)
    payload.pop("tags"); payload.pop("source_refs")
    response = client.put(f"{BASE}/{qid}", json=payload, headers=headers)
    assert response.status_code == 200, response.json()
    assert response.json()["status"] == "retired"
    assert response.json()["tags"] == before["tags"]
    assert response.json()["source_refs"] == before["source_refs"]
