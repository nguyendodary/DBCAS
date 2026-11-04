"""DN contract regressions; existing team tests remain unchanged."""
from app.main import app


def test_contract_describes_guards_and_actual_validation(client):
    contract = app.openapi()
    operations = [op for path in contract["paths"].values() for method, op in path.items()
                  if method in {"get", "post", "put", "patch", "delete"}]
    assert any(op.get("x-required-roles") == ["Administrator"] for op in operations)
    assert any(op.get("x-required-roles") == ["Learner"] for op in operations)
    assert "security" not in contract["paths"]["/api/v1/auth/login"]["post"]
    me = contract["paths"]["/api/v1/auth/me"]["get"]
    assert me["security"] == [{"BearerAuth": []}]
    assert me["responses"]["422"]["content"]["application/json"]["schema"]["$ref"].endswith("ErrorEnvelope")
    response = client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["details"]


def test_practice_schema_documents_count_and_selection_constraints():
    from app.services.practice_config import MIN_QUESTIONS, DEFAULT_QUESTIONS, MAX_QUESTIONS
    properties = app.openapi()["components"]["schemas"]["PracticeStart"]["properties"]
    assert properties["question_count"]["minimum"] == MIN_QUESTIONS
    assert properties["question_count"]["default"] == DEFAULT_QUESTIONS
    assert properties["question_count"]["maximum"] == MAX_QUESTIONS
    assert properties["source"]["enum"] == ["bank", "ai"]
    assert properties["difficulties"]["items"]["enum"] == ["EASY", "MEDIUM", "HARD"]
    assert properties["concept_ids"]["uniqueItems"] is True
    assert properties["difficulties"]["uniqueItems"] is True
