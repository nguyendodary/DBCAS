"""Describe the runtime error envelope and authorization dependencies in OpenAPI."""
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute, iter_route_contexts


def _dependencies(dependant):
    yield dependant.call
    for child in dependant.dependencies:
        yield from _dependencies(child)


def install_openapi(app: FastAPI) -> None:
    def contract():
        if app.openapi_schema is not None:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        components = schema.setdefault("components", {})
        components.setdefault("securitySchemes", {})["BearerAuth"] = {
            "type": "http", "scheme": "bearer", "bearerFormat": "JWT",
        }
        components.setdefault("schemas", {})["ErrorEnvelope"] = {
            "type": "object", "required": ["error"], "properties": {
                "error": {"type": "object", "required": ["code", "message"],
                          "properties": {"code": {"type": "string"},
                                         "message": {"type": "string"}, "details": {}}},
            },
        }
        for route in iter_route_contexts(app.routes):
            if not isinstance(route.original_route, APIRoute) or not route.include_in_schema:
                continue
            calls = list(_dependencies(route.dependant))
            protected = any(getattr(call, "__name__", "") == "get_current_account" for call in calls)
            roles = sorted({role for call in calls for role in getattr(call, "required_roles", ())})
            for method in route.methods:
                operation = schema["paths"][route.path_format][method.lower()]
                if protected:
                    operation["security"] = [{"BearerAuth": []}]
                    operation["x-required-roles"] = roles
                    operation["x-role-manager"] = any(
                        getattr(call, "__name__", "") == "require_role_manager" for call in calls
                    )
                    operation["parameters"] = [p for p in operation.get("parameters", [])
                                               if p.get("name", "").lower() != "authorization"]
                if route.path.startswith("/api/"):
                    statuses = {400: "Invalid operation", 404: "Resource not found",
                                409: "State conflict", 422: "Request validation failed",
                                429: "Rate limit exceeded", 500: "Unexpected failure",
                                502: "Provider returned an invalid response",
                                503: "Dependency unavailable"}
                    if protected:
                        statuses.update({401: "Missing, expired or invalid access token", 403: "Insufficient role or ownership"})
                    elif route.path in {"/api/v1/auth/login", "/api/v1/auth/oauth/complete"}:
                        statuses.update({401: "Invalid credentials or sign-in handoff", 403: "Account is disabled"})
                    for status, description in statuses.items():
                        operation.setdefault("responses", {})[str(status)] = {
                            "description": description,
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorEnvelope"}}},
                        }
        app.openapi_schema = schema
        return schema

    app.openapi = contract
