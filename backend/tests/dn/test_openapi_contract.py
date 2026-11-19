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
    from app.services.practice_config import (
        MIN_QUESTIONS, DEFAULT_QUESTIONS, MAX_SINGLE_TYPE_QUESTIONS,
    )
    contract = app.openapi()["components"]["schemas"]
    properties = contract["PracticeStart"]["properties"]
    assert properties["question_count"]["minimum"] == MIN_QUESTIONS
    assert properties["question_count"]["default"] == DEFAULT_QUESTIONS
    assert properties["question_count"]["maximum"] == MAX_SINGLE_TYPE_QUESTIONS
    assert "PracticeMix" in contract
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


def test_user_review_and_result_schemas_exclude_private_admin_fields():
    contract = app.openapi()
    schemas = contract["components"]["schemas"]
    paths = contract["paths"]
    review_path = paths["/api/v1/sessions/{session_id}/review-request"]

    def response_schema(operation, status="200"):
        return operation["responses"][status]["content"]["application/json"]["schema"]

    user_ref = {"$ref": "#/components/schemas/UserReviewRequestView"}
    admin_ref = {"$ref": "#/components/schemas/ReviewRequestView"}
    assert response_schema(review_path["post"]) == user_ref
    assert response_schema(review_path["post"], "201") == user_ref
    assert response_schema(review_path["get"])["anyOf"] == [user_ref, admin_ref]
    assert schemas["UserReviewRequestView"]["properties"]["v2_state"]["enum"] == [
        "NONE", "ANALYSIS_PENDING", "ANALYSIS_FAILED_V1_KEPT", "OFFICIAL",
    ]
    assert schemas["UserReviewRequestView"]["properties"]["v2_state"]["readOnly"] is True
    admin = paths["/api/v1/admin/review-requests/{review_request_id}/analysis-retry"]["post"]
    assert admin["x-required-roles"] == ["Administrator"]
    assert response_schema(admin)["$ref"] == "#/components/schemas/ReviewRequestDetail"

    def property_names(node, seen):
        if isinstance(node, list):
            for child in node:
                yield from property_names(child, seen)
        if isinstance(node, dict):
            ref = node.get("$ref")
            if ref and ref not in seen:
                seen.add(ref)
                yield from property_names(schemas[ref.rsplit("/", 1)[-1]], seen)
            yield from node.get("properties", {})
            for child in node.values():
                yield from property_names(child, seen)

    private = {"claimed_by", "resolved_by", "resolution_note", "analysis_status", "analysis_error",
               "prompt_text", "model_identifier", "analysis", "admin_note", "admin_id"}
    for ref in (user_ref, *(response_schema(paths[path]["get"]) for path in (
        "/api/v1/sessions", "/api/v1/sessions/{session_id}", "/api/v1/evaluations/attempts/{session_id}",
    ))):
        assert private.isdisjoint(property_names(ref, set()))
