"""An administrator cannot publish content rejected by the common bank gate."""
from copy import deepcopy

import pytest

from app.schemas import QuestionUpsertRequest
from app.services.practice_corpus import template_pack
from test_admin_questions import _admin, _concept

BASE = "/api/v1/admin/questions"


def payload(db, kind):
    concept = _concept(db, "SQL-SELECT")
    db.commit()
    item = deepcopy(next(q for q in template_pack()["questions"] if q["key"] == f"case-sql-select-easy-1-{kind}"))
    item["concept_ids"] = [concept.concept_id]
    return {k: v for k, v in item.items() if k in QuestionUpsertRequest.model_fields}


@pytest.mark.parametrize("kind,defect", [("mcq", "references"), ("mcq", "explanation"),
    ("essay", "sample"), ("sql", "empty_edge"), ("sql", "environment")])
def test_publication_rejects_every_common_content_contract_violation(client, db_session, kind, defect):
    headers = _admin(client, db_session)
    body = payload(db_session, kind)
    if defect == "references": body["source_refs"] = []
    if defect == "explanation": body["explanation"] = ""
    if defect == "sample": body["reference_answer"] = "..."
    if defect == "empty_edge":
        body["datasets"][1]["setup_sql"] = body["datasets"][1]["setup_sql"].split("INSERT INTO")[0]
        body["datasets"][1]["expected_result"]["rows"] = []
    if defect == "environment":
        body["reference_answer"] = "SELECT CURRENT_USER"
        for dataset in body["datasets"]:
            dataset["expected_result"] = {"columns": ["current_user"], "rows": [["learner_ro"]]}
    created = client.post(BASE, headers=headers, json=body)
    assert created.status_code == 201, created.text  # Incomplete drafts remain editable.
    qid = created.json()["question_id"]
    rejected = client.patch(f"{BASE}/{qid}", headers=headers, json={"status": "validated"})
    assert rejected.status_code == 422, rejected.text
    assert rejected.json()["error"]["code"] == "question_incomplete"
    assert client.get(f"{BASE}/{qid}", headers=headers).json()["status"] == "draft"


def test_edit_demotes_and_cannot_bypass_the_common_revalidation_gate(client, db_session):
    headers = _admin(client, db_session)
    body = payload(db_session, "mcq")
    created = client.post(BASE, headers=headers, json=body)
    qid = created.json()["question_id"]
    assert client.patch(f"{BASE}/{qid}", headers=headers, json={"status": "validated"}).status_code == 200
    body["explanation"] = ""
    edited = client.put(f"{BASE}/{qid}", headers=headers, json=body)
    assert edited.status_code == 200 and edited.json()["status"] == "draft"
    assert client.patch(f"{BASE}/{qid}", headers=headers, json={"status": "validated"}).status_code == 422
