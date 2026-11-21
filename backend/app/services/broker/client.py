"""API-side broker client and the standalone B1 service app.

The client is a no-op returning ``None`` while SANDBOX_BROKER is OFF. The
standalone app is never mounted into the main API, so the default OpenAPI
surface is unchanged. Its transport is an in-process stub; B2 replaces it with
the authenticated channel.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .service import BrokerError, BrokerService, validate_broker_config


class BrokerClient:
    def __init__(self, settings):
        validate_broker_config(settings)
        self.settings = settings
        self.service = BrokerService(settings)

    def health(self):
        return self.service.health()

    def call(self, body):
        response = self.service.handle(body, self.settings.sandbox_broker_peer_identity)
        return response.model_dump(mode="json")


def build_broker_client(settings):
    return BrokerClient(settings) if settings.sandbox_broker else None


def create_app(settings):
    validate_broker_config(settings)
    service = BrokerService(settings)
    app = FastAPI(title="DBCAS executor broker (B1 stub)")

    @app.get("/health")
    def health():
        return service.health()

    @app.post("/rpc")
    async def rpc(request: Request):
        body = await request.json()
        try:
            response = service.handle(body, settings.sandbox_broker_peer_identity)
        except BrokerError as exc:
            status = 403 if "capability" in exc.code or "peer" in exc.code else 409
            return JSONResponse(status_code=status, content={
                "error": {"code": exc.code, "message": exc.message},
            })
        return response.model_dump(mode="json")

    return app
