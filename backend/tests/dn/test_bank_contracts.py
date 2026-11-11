from historical_assessment_api import historical_client as client
"""DN pagination/classification and curated adaptive pool API regressions."""
from sqlalchemy import select

from app.models import Account, CloConcept, CourseLearningOutcome
from app.repositories import AssessmentRepository
from test_admin_questions import _admin, _concept, _mcq_payload
from test_admin_assessments import _payload

BASE = "/api/v1/admin"


def test_clo_topic_search_pagination_and_bounds(client, db_session):
    headers = _admin(client, db_session)
    concept = _concept(db_session, "DN-QUERY")
    db_session.commit()
    admin_id = db_session.scalar(select(Account.account_id))
    clo = CourseLearningOutcome(clo_code="DN-CLO", title="Query", created_by=admin_id)
    db_session.add(clo)
    db_session.flush()
    db_session.add(CloConcept(clo_id=clo.clo_id, concept_id=concept.concept_id, status="confirmed"))
    db_session.commit()
    ids = []
    for number in range(3):
        body = _mcq_payload(concept.concept_id)
        body["prompt"] = f"DN searchable query {number}"
        response = client.post(BASE + "/questions", json=body, headers=headers)
        assert response.status_code == 201
        ids.append(response.json()["question_id"])
    url = BASE + f"/questions?clo_id={clo.clo_id}&topic=SQL%20Querying&q=searchable&limit=1&offset=1"
    assert [q["question_id"] for q in client.get(url, headers=headers).json()] == [ids[1]]
    assert client.get(BASE + "/questions?topic=unknown", headers=headers).json() == []
    for suffix in ("limit=0", "limit=101", "offset=-1", "difficulty=6"):
        assert client.get(BASE + "/questions?" + suffix, headers=headers).status_code == 422


def test_curated_pool_is_used_and_invalid_replacement_rolls_back(client, db_session):
    headers = _admin(client, db_session)
    concept = _concept(db_session, "DN-POOL")
    db_session.commit()
    ids = []
    for _ in range(2):
        response = client.post(BASE + "/questions", json=_mcq_payload(concept.concept_id), headers=headers)
        qid = response.json()["question_id"]
        assert client.patch(BASE + f"/questions/{qid}", json={"status": "validated"}, headers=headers).status_code == 200
        ids.append(qid)
    created = client.post(BASE + "/assessments", json=_payload(concept.concept_id), headers=headers)
    assert created.status_code == 201
    aid = created.json()["assessment_id"]
    url = BASE + f"/assessments/{aid}/questions"
    assert client.put(url, json={"question_ids": [ids[0]]}, headers=headers).status_code == 200
    db_session.expire_all()
    repo = AssessmentRepository(db_session)
    assert [q.question_id for q in repo.eligible_questions(repo.get_assessment(aid), set())] == [ids[0]]
    assert client.put(url, json={"question_ids": [999999]}, headers=headers).status_code == 422
    assert client.get(url, headers=headers).json()["question_ids"] == [ids[0]]
    assert client.put(url, json={"question_ids": [ids[0], ids[0]]}, headers=headers).status_code == 422
    assert client.delete(BASE + f"/questions/{ids[0]}", headers=headers).status_code == 409
    cloned = repo.clone_assessment(repo.get_assessment(aid))
    db_session.commit()
    assert client.get(BASE + f"/assessments/{cloned.assessment_id}/questions", headers=headers).json()["question_ids"] == [ids[0]]
    assert client.put(url, json={"question_ids": []}, headers=headers).status_code == 200
    db_session.expire_all()
    assert len(repo.eligible_questions(repo.get_assessment(aid), set())) == 2
    assert client.get(BASE + "/assessments?limit=1&q=Midterm&status=draft", headers=headers).json()[0]["assessment_id"] == aid
    assert client.get(url).status_code == 401
