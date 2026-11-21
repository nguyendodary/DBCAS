"""PR-B1 broker: fixed schema, capability auth, replay guard, audit, stub run.

No Docker call, socket bind, database write or student SQL execution happens
here. The executor migration is B2.
"""
import base64
import hashlib
import hmac
import json
import logging
import re
import time

from .admission import BrokerAdmission
from .errors import BrokerError
from .schemas import BrokerAuditRecord, BrokerExecutionRequest, BrokerRequest, BrokerResponse

logger = logging.getLogger("dbcas.broker")
audit_logger = logging.getLogger("dbcas.broker.audit")

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_TEMPLATE = {
    "network": "none", "read_only_root": True, "uid": 10001, "gid": 10001,
    "cap_drop": ["ALL"], "no_new_privileges": True, "pids_limit": 128,
    "memory_mb": 256, "cpus": 1,
}


def validate_broker_config(settings):
    """Fail closed when the flag is ON; do nothing when it is OFF."""
    if not settings.sandbox_broker:
        return
    problems = []
    if not settings.sandbox_broker_issuer_key.strip():
        problems.append("SANDBOX_BROKER_ISSUER_KEY")
    if not settings.sandbox_broker_dataset_digests:
        problems.append("SANDBOX_BROKER_DATASET_DIGESTS")
    if any(not _SHA256.match(value)
           for value in settings.sandbox_broker_dataset_digests.values()):
        problems.append("SANDBOX_BROKER_DATASET_DIGESTS(digest)")
    if not settings.sandbox_broker_allowed_images:
        problems.append("SANDBOX_BROKER_ALLOWED_IMAGES")
    if any(not _SHA256.match(value)
           for value in settings.sandbox_broker_allowed_images.values()):
        problems.append("SANDBOX_BROKER_ALLOWED_IMAGES(digest)")
    if settings.sandbox_broker_template != _REQUIRED_TEMPLATE:
        problems.append("SANDBOX_BROKER_TEMPLATE")
    if settings.deployment_mode in ("staging", "production"):
        if settings.sandbox_broker_channel != "mtls":
            problems.append("SANDBOX_BROKER_CHANNEL")
        for name in ("sandbox_broker_client_cert_path", "sandbox_broker_client_key_path",
                     "sandbox_broker_ca_cert_path"):
            if not getattr(settings, name).strip():
                problems.append(name.upper())
    if problems:
        raise ValueError("Incomplete broker configuration: " + ", ".join(sorted(set(problems))))


def _canonical(request):
    """Canonical request body used for capability binding and replay checks."""
    body = request.model_dump() if hasattr(request, "model_dump") else dict(request)
    body.pop("capability", None)
    body.pop("script", None)  # SQL text is never bound into a capability or audit record
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)


def _b64(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def issue_capability(request_body, settings):
    """Issue a short-lived, audience-bound HMAC capability for one request."""
    validate_broker_config(settings)
    body = {
        "iss": settings.sandbox_broker_issuer_id,
        "aud": "dbcas-broker",
        "exp": int(time.time()) + settings.sandbox_broker_capability_ttl_seconds,
        "request": json.loads(_canonical(request_body)),
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(settings.sandbox_broker_issuer_key.encode("utf-8"), raw, hashlib.sha256).digest()
    return _b64(raw) + "." + _b64(signature)


def verify_capability(request, settings, peer_identity):
    if peer_identity != settings.sandbox_broker_peer_identity:
        raise BrokerError("broker_peer_unauthorized", "Broker peer identity is not authorized")
    try:
        encoded, signature = request.capability.split(".", 1)
        raw = _unb64(encoded)
        expected = hmac.new(settings.sandbox_broker_issuer_key.encode("utf-8"), raw, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(signature)):
            raise ValueError("bad signature")
        body = json.loads(raw)
        if body.get("iss") != settings.sandbox_broker_issuer_id or body.get("aud") != "dbcas-broker":
            raise ValueError("bad issuer or audience")
        if int(body.get("exp", 0)) <= time.time():
            raise ValueError("expired")
        if body.get("request") != json.loads(_canonical(request)):
            raise ValueError("capability does not bind this request")
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise BrokerError("broker_capability_invalid", "Broker capability was rejected") from exc


class BrokerService:
    """Stateless skeleton except for a bounded in-memory replay ledger."""

    def __init__(self, settings):
        validate_broker_config(settings)
        self.settings = settings
        self._seen = {}
        self._max_seen = 1000  # bounded replay ledger
        self.admission = BrokerAdmission(
            settings.sandbox_broker_queue_size,
            max(1, settings.sandbox_broker_queue_size // 4),
            settings.sandbox_broker_admission_timeout_ms / 1000,
        )
        from .runtime import build_runtime
        self.runtime = build_runtime(settings)

    def _remember(self, key, value):
        if len(self._seen) >= self._max_seen:
            self._seen.pop(next(iter(self._seen)))
        self._seen[key] = value

    def health(self):
        return {
            "status": "ok" if self.settings.sandbox_broker else "disabled",
            "schema_version": self.settings.sandbox_broker_schema_version,
            "channel": self.settings.sandbox_broker_channel,
            "runtime": self.settings.sandbox_broker_runtime,
            "execution": "stub" if self.settings.sandbox_broker_runtime == "stub" else "constrained",
        }

    def execute(self, body, setup_sql, sql, *, grading=False):
        """B2 execution path: capability-checked, admitted, constrained, audited."""
        started = time.monotonic()
        request = None
        previous = None
        try:
            request = BrokerExecutionRequest.model_validate(body)
            verify_capability(request, self.settings, self.settings.sandbox_broker_peer_identity)
            if hashlib.sha256(sql.encode("utf-8")).hexdigest() != request.script_hash:
                raise BrokerError("broker_script_hash_mismatch", "SQL does not match the approved hash")
            if hashlib.sha256((setup_sql or "").encode("utf-8")).hexdigest() != request.setup_hash:
                raise BrokerError("broker_script_hash_mismatch", "Dataset setup does not match the approved hash")
            if self.settings.sandbox_broker_dataset_digests.get(request.dataset_id) != request.dataset_digest:
                raise BrokerError("broker_dataset_not_allowed", "Dataset digest is not allow-listed")
            canonical = _canonical(request)
            seen = self._seen.get(str(request.request_id))
            if seen and seen[0] == canonical and "result" in seen[1]:
                return seen[1]
            if seen and seen[0] != canonical:
                raise BrokerError("broker_replay_conflict", "Request id reused with a different payload")
            previous = self.admission.acquire(grading=grading)
            result = self.runtime.execute(setup_sql or "", sql)
            response = {
                "request_id": str(request.request_id),
                "operation": request.operation,
                "status": "executed",
                "executed": True,
                "result_class": "executed",
                "duration_ms": int((time.monotonic() - started) * 1000),
                "result": result,
            }
            self._remember(str(request.request_id), (canonical, response))
            self._audit(request, "accepted", type("Audit", (), {
                "result_class": response["result_class"],
                "duration_ms": response["duration_ms"],
            })())
            return response
        except BrokerError as exc:
            if request is not None:
                self._audit_failure(body, exc.code)
            raise
        finally:
            if previous is not None:
                self.admission.release(previous, grading=grading)

    def reap(self):
        return self.runtime.reap()

    def handle(self, body, peer_identity):
        started = time.monotonic()
        try:
            request = BrokerRequest.model_validate(body)
            verify_capability(request, self.settings, peer_identity)
            if self.settings.sandbox_broker_dataset_digests.get(request.dataset_id) != request.dataset_digest:
                raise BrokerError("broker_dataset_not_allowed", "Dataset digest is not allow-listed")
            if self.settings.sandbox_broker_template != _REQUIRED_TEMPLATE:
                raise BrokerError("broker_template_not_allowed", "Broker template is not allow-listed")
            canonical = _canonical(request)
            previous = self._seen.get(str(request.request_id))
            if previous:
                fingerprint, response = previous
                if fingerprint != canonical:
                    raise BrokerError("broker_replay_conflict", "Request id reused with a different payload")
                return response
            response = BrokerResponse(
                request_id=request.request_id,
                operation=request.operation,
                duration_ms=int((time.monotonic() - started) * 1000),
            )
            self._remember(str(request.request_id), (canonical, response))
            self._audit(request, "accepted", response)
            return response
        except BrokerError as exc:
            self._audit_failure(body, exc.code)
            raise
        except Exception as exc:
            error = BrokerError("broker_request_invalid", "Broker request was rejected")
            self._audit_failure(body, error.code)
            raise error from exc

    def _audit(self, request, outcome, response):
        record = BrokerAuditRecord(
            request_id=request.request_id,
            operation=request.operation,
            outcome=outcome,
            dataset_id=request.dataset_id,
            script_hash=request.script_hash,
            requester=request.requester,
            policy_version=self.settings.sandbox_broker_schema_version,
            result_class=response.result_class,
            duration_ms=response.duration_ms,
            retention_days=self.settings.sandbox_broker_audit_retention_days,
        )
        audit_logger.info(json.dumps(record.model_dump(mode="json"), sort_keys=True))

    def _audit_failure(self, body, code):
        audit_logger.info(json.dumps({
            "outcome": "rejected",
            "reason": code,
            "request_id": str(body.get("request_id")) if isinstance(body, dict) else None,
            "retention_days": self.settings.sandbox_broker_audit_retention_days,
        }, sort_keys=True))
