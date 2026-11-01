"""Real disposable offline containers, resource isolation and failure cleanup."""
import json
from pathlib import Path
import subprocess
import time

import pytest

from app.config import get_settings
from app.services.ephemeral_sandbox import EphemeralSandboxRunner, docker_cli
from app.services.sandbox_runner import SandboxError, build_sandbox_runner


@pytest.fixture(scope="module", autouse=True)
def executor_image():
    root = Path(__file__).resolve().parents[3]
    subprocess.run([*docker_cli(), "build", "-q", "-f", "sandbox/Dockerfile.ephemeral",
                    "-t", "dbcas-sql-ephemeral:local", "."], cwd=root, check=True, timeout=300, capture_output=True)


@pytest.fixture()
def runner():
    settings = get_settings().model_copy(update={"sandbox_mode": "ephemeral"})
    runner = build_sandbox_runner(settings)
    assert isinstance(runner, EphemeralSandboxRunner)
    yield runner
    runner.cleanup_datasets()


def test_offline_container_limits_typed_execution_and_cleanup(runner):
    assert runner.is_ready()
    schema = runner.provision_dataset("CREATE TABLE t(id int, name text); INSERT INTO t VALUES (1,'one'),(2,'two');")
    name = runner.leases[schema]
    config = json.loads(runner._docker("inspect", name))[0]
    host = config["HostConfig"]
    assert host["NetworkMode"] == "none"
    assert host["Memory"] == 256 * 1024 * 1024 and host["NanoCpus"] == 1_000_000_000
    assert host["ReadonlyRootfs"] and host["PidsLimit"] == 128
    assert host["CapDrop"] == ["ALL"] and "no-new-privileges:true" in host["SecurityOpt"]
    assert not host["PortBindings"]
    assert all(m["Type"] == "tmpfs" for m in config["Mounts"])
    probe = runner._docker("exec", name, "/opt/runner/bin/python", "-c",
                           "import socket; s=socket.socket(); s.settimeout(0.5); print(s.connect_ex(('1.1.1.1',53)))")
    assert int(probe) != 0
    result = runner.execute("SELECT id,name FROM t ORDER BY id", schema=schema)
    assert result.success and result.rows == [[1, "one"], [2, "two"]]
    assert result.column_types == ["number", "text"]
    assert runner.execute("DROP TABLE t", schema=schema).error_type == "not_a_select"
    runner.drop_dataset(schema)
    assert not runner._docker("ps", "-aq", "--filter", "name=" + name)


def test_failure_paths_cleanup_and_environment(runner, monkeypatch):
    assert runner.validate_environment() == []
    assert runner.execute("SELECT 1").rows == [[1]]
    assert runner.execute("SELECT 1; SELECT 2").success is False
    with pytest.raises(SandboxError):
        runner.provision_dataset("CREATE EXTENSION dblink;")
    original = runner._call
    def broken(*args, **kwargs):
        raise SandboxError("sandbox_unavailable", "Simulated transport loss")
    monkeypatch.setattr(runner, "_call", broken)
    with pytest.raises(SandboxError):
        runner.execute("SELECT 1")
    assert not runner.deadlines
    monkeypatch.setattr(runner, "_call", original)
    assert runner.execute("SELECT 2").rows == [[2]]


def test_statement_timeout_and_watchdog_remove_abandoned_lease(runner):
    runner.settings = runner.settings.model_copy(update={"sandbox_statement_timeout_ms": 100,
                                                       "sandbox_container_lifetime_seconds": 10})
    result = runner.execute("WITH RECURSIVE n AS (SELECT 1 AS x UNION ALL SELECT x+1 FROM n WHERE x<100000000) SELECT max(x) FROM n")
    assert result.error_type == "timeout"
    schema = runner.provision_dataset("CREATE TABLE t(id int);")
    name = runner.leases[schema]
    # Simulate an abandoned host lease. No explicit container removal occurs
    # until Docker confirms the in-container watchdog has stopped PID 1.
    until = time.monotonic() + 15
    while runner._docker("ps", "-aq", "--filter", "name=" + name) and time.monotonic() < until:
        time.sleep(0.25)
    assert not runner._docker("ps", "-aq", "--filter", "name=" + name)
    runner.drop_dataset(schema)
