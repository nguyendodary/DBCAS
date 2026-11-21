"""PR-B1 broker skeleton contract tests; no Docker or database is used."""
import json
import logging
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.services.broker.client import build_broker_client, create_app
from app.services.broker.schemas import BrokerRequest
from app.services.broker.service import BrokerError, BrokerService, issue_capability

DATASET_ID = "ds-approved"
DATASET_DIGEST = "a" * 64
IMAGE_DIGEST = "b" * 64
SCRIPT_HASH = "c" * 64
PEER = "dbcas-api"


def complete_settings(**updates):
    settings = get_settings().model_copy(update={
        "sandbox_broker": True,
        "sandbox_broker_issuer_key": "unit-test-issuer-key-not-a-real-secret",
        "sandbox_broker_dataset_digests": {DATASET_ID: DATASET_DIGEST},
        "sandbox_broker_allowed_images": {"dbcas-sql-ephemeral:local": IMAGE_DIGEST},
    })
    return settings.model_copy(update=updates)


def body_for(settings, **updates):
    body = {
        "version": 1,
        "operation": "run",
        "request_id": uuid4(),
        "dataset_id": DATASET_ID,
        "dataset_digest": DATASET_DIGEST,
        "script_hash": SCRIPT_HASH,
        "mode": "read_only",
        "limits": {"wall_ms": 5000},
        "requester": "opaque-learner-42",
    }
    body.update(updates)
    body["capability"] = issue_capability(body, settings)
    return body


def test_schema_rejects_unknown_fields_and_unapproved_values():
    for bad in (
        {"image": "evil:latest"},
        {"operation": "exec"},
        {"mode": "writable"},
        {"limits": {"wall_ms": 5001}},
        {"dataset_digest": "short"},
    ):
        with pytest.raises(ValidationError):
            BrokerRequest.model_validate(body_for(complete_settings(), **bad))


def test_capability_peer_identity_and_replay():
    settings = complete_settings()
    service = BrokerService(settings)
    body = body_for(settings)
    assert service.handle(body, PEER).executed is False
    # Exact retransmission is idempotent.
    assert service.handle(body, PEER) == service.handle(body, PEER)

    forged = dict(body, capability=body["capability"][:-2] + "xy")
    with pytest.raises(BrokerError) as exc:
        service.handle(forged, PEER)
    assert exc.value.code == "broker_capability_invalid"

    with pytest.raises(BrokerError) as exc:
        service.handle(body, "other-service")
    assert exc.value.code == "broker_peer_unauthorized"

    changed = dict(body, request_id=body["request_id"], script_hash="d" * 64)
    changed["capability"] = issue_capability(changed, settings)
    with pytest.raises(BrokerError) as exc:
        service.handle(changed, PEER)
    assert exc.value.code == "broker_replay_conflict"


def test_expired_capability_is_rejected(monkeypatch):
    settings = complete_settings()
    service = BrokerService(settings)
    body = body_for(settings)
    import app.services.broker.service as service_module
    real_time = service_module.time.time()
    monkeypatch.setattr(
        service_module.time, "time",
        lambda: real_time + settings.sandbox_broker_capability_ttl_seconds + 1,
    )
    with pytest.raises(BrokerError) as exc:
        service.handle(body, PEER)
    assert exc.value.code == "broker_capability_invalid"


def test_dataset_and_template_allow_lists():
    settings = complete_settings()
    service = BrokerService(settings)
    wrong = body_for(settings, dataset_digest="e" * 64)
    with pytest.raises(BrokerError) as exc:
        service.handle(wrong, PEER)
    assert exc.value.code == "broker_dataset_not_allowed"

    weakened = complete_settings(sandbox_broker_template={
        "network": "bridge", "read_only_root": True, "uid": 10001, "gid": 10001,
        "cap_drop": ["ALL"], "no_new_privileges": True, "pids_limit": 128,
        "memory_mb": 256, "cpus": 1,
    })
    with pytest.raises(ValueError):
        BrokerService(weakened)


@pytest.mark.parametrize("mode,flag,complete,channel,accepted", [
    ("development", False, False, "unix", True),
    ("development", True, True, "unix", True),
    ("development", True, False, "unix", False),
    ("staging", True, True, "unix", False),
    ("staging", True, True, "mtls", True),
    ("production", True, True, "mtls", True),
    ("production", True, True, "unix", False),
])
def test_fail_closed_config_matrix(mode, flag, complete, channel, accepted):
    settings = get_settings().model_copy(update={
        "deployment_mode": mode,
        "sandbox_broker": flag,
        "sandbox_broker_channel": channel,
    })
    if complete:
        settings = settings.model_copy(update={
            "sandbox_broker_issuer_key": "unit-test-issuer-key-not-a-real-secret",
            "sandbox_broker_dataset_digests": {DATASET_ID: DATASET_DIGEST},
            "sandbox_broker_allowed_images": {"dbcas-sql-ephemeral:local": IMAGE_DIGEST},
            "sandbox_broker_client_cert_path": "/etc/dbcas/client.pem",
            "sandbox_broker_client_key_path": "/etc/dbcas/client.key",
            "sandbox_broker_ca_cert_path": "/etc/dbcas/ca.pem",
        })
    if accepted:
        BrokerService(settings)
    else:
        with pytest.raises(ValueError):
            BrokerService(settings)


def test_audit_log_has_no_sensitive_data(caplog):
    settings = complete_settings()
    service = BrokerService(settings)
    body = body_for(settings)
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="dbcas.broker.audit"):
        service.handle(body, PEER)
    text = "\n".join(record.getMessage() for record in caplog.records)
    assert SCRIPT_HASH in text
    assert "SELECT" not in text and "secret" not in text
    assert "learner-42@example.com" not in text
    record = json.loads(text.strip().splitlines()[-1])
    assert record["outcome"] == "accepted"
    assert record["script_hash"] == SCRIPT_HASH
    assert record["retention_days"] == 30
    assert set(record) == {
        "request_id", "operation", "outcome", "dataset_id", "script_hash",
        "requester", "policy_version", "result_class", "duration_ms",
        "retention_days",
    }


def test_audit_rejection_never_echoes_sql_text(caplog):
    settings = complete_settings()
    service = BrokerService(settings)
    body = body_for(settings)
    sql = "SELECT secret_column FROM private_table WHERE token='learner-42'"
    body["sql"] = sql  # unknown field: schema must reject it
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="dbcas.broker.audit"):
        with pytest.raises(BrokerError):
            service.handle(body, PEER)
    text = "\n".join(record.getMessage() for record in caplog.records)
    assert sql not in text
    assert "secret_column" not in text
    assert "learner-42" not in text


def test_flag_name_and_ttl_owner_decisions():
    fields = Settings.model_fields
    assert "sandbox_broker" in fields and "broker_enabled" not in fields
    assert fields["sandbox_broker"].default is False
    assert fields["sandbox_broker_capability_ttl_seconds"].default == 300
    assert fields["sandbox_broker_audit_retention_days"].default == 30
    assert "sandbox_broker_audit_include_sql_text" not in fields


def test_health_endpoint_and_flag_off_client():
    settings = complete_settings()
    client = TestClient(create_app(settings))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok", "schema_version": 1, "channel": "unix",
        "runtime": "stub", "execution": "stub",
    }
    assert build_broker_client(get_settings()) is None
