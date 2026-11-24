"""B2 tests: no Docker is used; the runtime is injected as a fake."""
import hashlib
import logging

import pytest

from app.config import Settings, get_settings
from app.services.broker.client import (
    BrokerClient,
    build_broker_client,
    get_broker_service,
    reset_broker_service,
)
from app.services.broker.runtime import ConstrainedRuntime, FakeRuntime
from app.services.broker.service import BrokerError
from app.services.ephemeral_sandbox import EphemeralSandboxRunner

IMAGE = "dbcas-sql-ephemeral:local"
DIGEST = "a" * 64
DATA_DIGEST = "b" * 64


def settings_for(**updates):
    return get_settings().model_copy(update={
        "sandbox_broker": True,
        "sandbox_broker_issuer_key": "unit-test-issuer-key",
        "sandbox_broker_dataset_digests": {"learner_dataset": DATA_DIGEST},
        "sandbox_broker_allowed_images": {IMAGE: DIGEST},
        "sandbox_broker_image_digest": DIGEST,
        "sandbox_broker_runtime": "docker",
        **updates,
    })


@pytest.fixture(autouse=True)
def clean_service():
    reset_broker_service()
    yield
    reset_broker_service()


def test_flag_off_is_byte_identical():
    off = Settings(_env_file=None)
    assert off.sandbox_broker is False
    assert off.sandbox_broker_runtime == "stub"
    assert build_broker_client(off) is None
    assert EphemeralSandboxRunner(off)._broker is None
    assert get_broker_service(off) is None


def test_service_is_process_shared_and_grading_has_separate_capacity():
    settings = settings_for(sandbox_broker_queue_size=1, sandbox_broker_admission_timeout_ms=50)
    first = BrokerClient(settings)
    second = BrokerClient(settings)
    assert first.service is second.service is get_broker_service(settings)
    admission = first.service.admission
    previous = admission.acquire()
    with pytest.raises(BrokerError) as exc:
        admission.acquire()
    assert exc.value.code == "broker_busy"
    grading_previous = admission.acquire(grading=True)
    admission.release(grading_previous, grading=True)
    admission.release(previous)


def test_execution_audit_never_contains_sql(caplog):
    settings = settings_for()
    service = get_broker_service(settings)
    service.runtime = FakeRuntime(settings)
    client = BrokerClient(settings)
    sql = "SELECT secret_column FROM private_table WHERE token='learner-42'"
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="dbcas.broker.audit"):
        response = client.execute_sql("CREATE TABLE t(id int)", sql)
    assert response["executed"] is True
    assert response["result"]["rows"] == [[1]]
    text = "\n".join(record.getMessage() for record in caplog.records)
    assert sql not in text and "secret_column" not in text and "learner-42" not in text
    assert hashlib.sha256(sql.encode()).hexdigest() in text


def test_script_execution_uses_multi_statement_operation():
    settings = settings_for()
    service = get_broker_service(settings)
    service.runtime = FakeRuntime(settings)
    client = BrokerClient(settings)
    response = client.execute_script("CREATE TABLE t(id int)", "SELECT 1; SELECT 2")
    assert response["operation"] == "run_sql_script"
    assert response["executed"] is True
    assert response["result"]["rows"] == [[1]]


def test_runner_script_delegates_when_flag_on():
    settings = settings_for()
    runner = EphemeralSandboxRunner(settings)
    import app.services.broker.client as broker_client
    broker_client.reset_broker_service()
    runner._broker.service.runtime = FakeRuntime(settings)
    schema = runner.provision_dataset("CREATE TABLE t(id int)")
    try:
        result = runner.execute_script("SELECT 1; SELECT 2", schema=schema)
        assert result.rows == [[1]]
    finally:
        runner.drop_dataset(schema)
        broker_client.reset_broker_service()


def test_docker_runtime_requires_an_allow_listed_image_digest():
    for digest in ("", "c" * 64):
        settings = settings_for(sandbox_broker_image_digest=digest)
        with pytest.raises(ValueError) as exc:
            get_broker_service(settings)
        assert "SANDBOX_BROKER_IMAGE_DIGEST" in str(exc.value)


def test_writable_execution_cannot_bypass_the_broker():
    settings = settings_for(sandbox_writable=True)
    with pytest.raises(ValueError) as exc:
        get_broker_service(settings)
    assert "SANDBOX_WRITABLE(B3)" in str(exc.value)


def test_execution_rejects_bad_capability():
    settings = settings_for()
    service = get_broker_service(settings)
    service.runtime = FakeRuntime(settings)
    client = BrokerClient(settings)
    response = client.execute_sql("", "SELECT 1")
    body = {
        "version": 1, "operation": "run_sql", "request_id": response["request_id"],
        "dataset_id": "learner_dataset", "dataset_digest": DATA_DIGEST,
        "script_hash": hashlib.sha256(b"SELECT 1").hexdigest(),
        "setup_hash": hashlib.sha256(b"").hexdigest(), "script": "SELECT 1",
        "limits": {"wall_ms": 3000}, "requester": "opaque-learner",
        "capability": "invalid-capability-value",
    }
    from app.services.broker.schemas import BrokerExecutionRequest
    with pytest.raises(BrokerError) as exc:
        service.execute(body, "", "SELECT 1")
    assert exc.value.code == "broker_capability_invalid"


def test_execution_rejects_sql_hash_mismatch():
    settings = settings_for()
    service = get_broker_service(settings)
    service.runtime = FakeRuntime(settings)
    client = BrokerClient(settings)
    body = {
        "version": 1, "operation": "run_sql", "request_id": __import__("uuid").uuid4(),
        "dataset_id": "learner_dataset", "dataset_digest": DATA_DIGEST,
        "script_hash": hashlib.sha256(b"SELECT 1").hexdigest(),
        "setup_hash": hashlib.sha256(b"").hexdigest(),
        "script": "SELECT 2", "limits": {"wall_ms": 3000},
        "requester": "opaque-learner", "capability": "",
    }
    from app.services.broker.service import issue_capability
    body["capability"] = issue_capability({k: v for k, v in body.items() if k != "script"}, settings)
    with pytest.raises(BrokerError) as exc:
        service.execute(body, "", "SELECT 2")
    assert exc.value.code == "broker_script_hash_mismatch"


def test_constrained_runtime_arguments_and_reaper():
    calls = []

    def fake_docker(args, *, input=None, timeout=15):
        calls.append(args)
        if args[:2] == ["docker", "create"]:
            return "container-1"
        if args[:2] == ["docker", "exec"]:
            return '{"result": {"success": true, "columns": [], "rows": [], "row_count": 0}}'
        return ""

    settings = settings_for()
    runtime = ConstrainedRuntime(settings, docker=fake_docker)
    result = runtime.execute("CREATE TABLE t(id int)", "SELECT 1")
    assert result["success"] is True
    create = next(args for args in calls if args[:2] == ["docker", "create"])
    assert "--network" in create and create[create.index("--network") + 1] == "none"
    assert "--read-only" in create
    assert "--user" in create and create[create.index("--user") + 1] == "10001:10001"
    assert "--cap-drop" in create and create[create.index("--cap-drop") + 1] == "ALL"
    assert "--security-opt" in create
    assert create[create.index("--security-opt") + 1] == "no-new-privileges:true"
    assert "--pids-limit" in create and "--memory" in create and "--cpus" in create
    assert create.count("--tmpfs") == 3  # writable runtime dirs, no host mounts
    assert IMAGE in create
    runtime._leases["container-1"] = 0
    runtime.reap()
    assert any(args[:3] == ["docker", "rm", "-f"] for args in calls)


def test_runner_delegates_only_when_flag_on():
    enabled = settings_for()
    runner = EphemeralSandboxRunner(enabled)
    assert runner._broker is not None
    schema = runner.provision_dataset("CREATE TABLE t(id int)")
    assert schema.startswith("ds_broker_")
    runner._broker.service.runtime = FakeRuntime(enabled)
    result = runner.execute("SELECT 1", schema=schema)
    assert result.rows == [[1]]
    runner.drop_dataset(schema)
    assert schema not in runner._broker_datasets
