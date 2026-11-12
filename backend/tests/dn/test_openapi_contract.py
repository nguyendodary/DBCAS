"""DN contract regressions; existing team tests remain unchanged."""
import json
from pathlib import Path

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


def test_every_json_success_has_a_schema_and_oauth_redirects_are_documented():
    contract = app.openapi()
    for path, item in contract["paths"].items():
        for method, operation in item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            for code, response in operation["responses"].items():
                if code.startswith("2") and code != "204":
                    assert response.get("content", {}).get("application/json", {}).get("schema"), (method, path, code)
    for suffix in ("start", "callback"):
        operation = contract["paths"][f"/api/v1/auth/oauth/{{provider}}/{suffix}"]["get"]
        assert "302" in operation["responses"] and "200" not in operation["responses"]
    for path in ("/api/v1/auth/login", "/api/v1/auth/oauth/complete"):
        assert "401" in contract["paths"][path]["post"]["responses"]


def test_generated_inventory_records_response_models_for_main_app_routes():
    """The inventory promises response models, including routes in main.py."""
    inventory = json.loads(
        (Path(__file__).resolve().parents[3] / "docs/inventory/api-routes.json").read_text(encoding="utf-8")
    )
    models = {(route["method"], route["path"]): route["response_model"] for route in inventory["routes"]}
    assert models[("GET", "/health")] == "StatusResult"
    assert models[("GET", "/api/v1/ping")] == "PingResult"
    assert models[("GET", "/readiness")] == "ReadinessResult"
