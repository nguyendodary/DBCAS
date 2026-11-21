"""API-side broker client and the standalone B1 service app.

The client is a no-op returning ``None`` while SANDBOX_BROKER is OFF. The
standalone app is never mounted into the main API, so the default OpenAPI
surface is unchanged. Its transport is an in-process stub; B2 replaces it with
the authenticated channel.
"""
import hashlib
import threading
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .service import BrokerError, BrokerService, issue_capability, validate_broker_config

_service_lock = threading.Lock()
_shared_service = None


def get_broker_service(settings):
    """One service per process: admission and replay state are process-shared."""
    global _shared_service
    if not settings.sandbox_broker:
        return None
    with _service_lock:
        if _shared_service is None:
            _shared_service = BrokerService(settings)
        return _shared_service


def reset_broker_service():
    global _shared_service
    with _service_lock:
        _shared_service = None


class BrokerClient:
    def __init__(self, settings):
        validate_broker_config(settings)
        self.settings = settings
        self.service = get_broker_service(settings)

    def health(self):
        return self.service.health()

    def call(self, body):
        response = self.service.handle(body, self.settings.sandbox_broker_peer_identity)
        return response.model_dump(mode="json")

    def execute_sql(self, setup_sql, sql, *, dataset_id="learner_dataset",
                    requester="opaque-learner", grading=False):
        """B2: run one learner statement through the constrained broker runtime."""
        digests = self.settings.sandbox_broker_dataset_digests
        if dataset_id not in digests:
            raise BrokerError("broker_dataset_not_allowed", "Dataset id is not allow-listed")
        body = {
            "version": 1,
            "operation": "run_sql",
            "request_id": uuid.uuid4(),
            "dataset_id": dataset_id,
            "dataset_digest": digests[dataset_id],
            "script_hash": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
            "setup_hash": hashlib.sha256((setup_sql or "").encode("utf-8")).hexdigest(),
            "script": sql,
            "limits": {"wall_ms": self.settings.sandbox_statement_timeout_ms},
            "requester": requester,
            "capability": "",
        }
        body["capability"] = issue_capability(
            {key: value for key, value in body.items() if key != "script"}, self.settings)
        return self.service.execute(body, setup_sql, sql, grading=grading)


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
