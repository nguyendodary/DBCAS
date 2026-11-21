"""Real-Docker broker runtime probes.

These tests run ONLY when SANDBOX_BROKER=true, SANDBOX_BROKER_RUNTIME=docker and
a Docker CLI is available (CI validation jobs). With the default OFF they are
skipped, so the normal suite stays byte-identical.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from app.config import get_settings
from app.services.broker.service import BrokerError
from app.services.broker.runtime import ConstrainedRuntime

pytestmark = pytest.mark.skipif(
    os.environ.get("SANDBOX_BROKER", "").lower() != "true"
    or os.environ.get("SANDBOX_BROKER_RUNTIME", "stub") != "docker"
    or shutil.which("docker") is None,
    reason="broker real-runtime probes require SANDBOX_BROKER=true and Docker",
)

ROOT = Path(__file__).resolve().parents[3]


def _cli(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          check=True, **kwargs).stdout.strip()


@pytest.fixture(scope="module")
def runtime():
    _cli(["docker", "build", "-q", "-f", "sandbox/Dockerfile.ephemeral",
          "-t", "dbcas-sql-ephemeral:local", "."])
    return ConstrainedRuntime(get_settings())


def _inspect(name):
    return json.loads(_cli(["docker", "inspect", name]))[0]


def test_network_egress_blocked(runtime):
    name = "dbcas-broker-probe-" + os.urandom(4).hex()
    try:
        runtime._docker(runtime._create_args(name))
        runtime._docker(["docker", "start", name])
        probe = runtime._docker([
            "docker", "exec", name, "/opt/runner/bin/python", "-c",
            "import socket; s=socket.socket(); s.settimeout(0.5); print(s.connect_ex(('1.1.1.1',53)))",
        ])
        assert int(probe) != 0
    finally:
        runtime._docker(["docker", "rm", "-f", name])


def test_memory_pids_and_readonly_rootfs_enforced(runtime):
    name = "dbcas-broker-probe-" + os.urandom(4).hex()
    try:
        runtime._docker(runtime._create_args(name))
        host = _inspect(name)["HostConfig"]
        assert host["Memory"] == runtime.settings.sandbox_broker_template["memory_mb"] * 1024 * 1024
        assert host["NanoCpus"] == runtime.settings.sandbox_broker_template["cpus"] * 1_000_000_000
        assert host["PidsLimit"] == runtime.settings.sandbox_broker_template["pids_limit"]
        assert host["ReadonlyRootfs"] is True
        assert host["NetworkMode"] == "none"
        assert host["CapDrop"] == ["ALL"]
        assert "no-new-privileges:true" in host["SecurityOpt"]
    finally:
        runtime._docker(["docker", "rm", "-f", name])


def test_cross_user_leases_are_isolated(runtime):
    names = []
    original = runtime._docker

    def capture(args, **kwargs):
        if args[:2] == ["docker", "create"]:
            names.append(args[args.index("--name") + 1])
        return original(args, **kwargs)

    runtime._docker = capture
    try:
        first = runtime.execute("CREATE TABLE t(id int); INSERT INTO t VALUES (1)", "SELECT id FROM t")
        second = runtime.execute("CREATE TABLE t(id int); INSERT INTO t VALUES (2)", "SELECT id FROM t")
        assert first["success"] is True and second["success"] is True
        assert len(set(names)) == 2
    finally:
        runtime._docker = original
        for name in names:
            runtime._docker(["docker", "rm", "-f", name])


def test_reaper_removes_expired_broker_lease(runtime):
    name = "dbcas-broker-probe-" + os.urandom(4).hex()
    try:
        runtime._docker(runtime._create_args(name))
        runtime._leases[name] = 0  # expired
        runtime.reap()
        listed = _cli(["docker", "ps", "-aq", "--filter", "name=" + name])
        assert listed == ""
    finally:
        runtime._docker(["docker", "rm", "-f", name])


def test_hash_mismatch_rejected_before_runtime(runtime):
    from app.services.broker.service import BrokerService, issue_capability
    from uuid import uuid4

    settings = get_settings()
    service = BrokerService(settings)
    digest = next(iter(settings.sandbox_broker_dataset_digests.values()))
    body = {
        "version": 1, "operation": "run_sql", "request_id": uuid4(),
        "dataset_id": next(iter(settings.sandbox_broker_dataset_digests)),
        "dataset_digest": digest, "script_hash": "0" * 64,
        "setup_hash": "0" * 64, "script": "SELECT 1",
        "limits": {"wall_ms": 3000}, "requester": "probe-user",
        "capability": "",
    }
    body["capability"] = issue_capability({k: v for k, v in body.items() if k != "script"}, settings)
    with pytest.raises(BrokerError) as exc:
        service.execute(body, "", "SELECT 1")
    assert exc.value.code == "broker_script_hash_mismatch"


def test_pids_limit_refuses_excess_processes(runtime):
    """Real-Docker proof that the allow-listed pids limit actually rejects forks.

    The allow-listed template uses 128 pids, so spawning 200 short-lived sleeps
    inside the container must hit the cgroup pids limit. This uses the real,
    unmodified ``_create_args`` flags; the limit is only made reachable quickly
    rather than by stressing the host for minutes.
    """
    name = "dbcas-broker-probe-" + os.urandom(4).hex()
    limit = runtime.settings.sandbox_broker_template["pids_limit"]
    try:
        runtime._docker(runtime._create_args(name))
        # Count inside the SAME exec: once the limit is saturated Docker cannot
        # admit a second exec process, so a separate counting exec is misleading.
        exceeded = subprocess.run(
            ["docker", "exec", name, "/bin/sh", "-c",
             "for i in $(seq 1 200); do sleep 30 & done; "
             "n=0; for p in /proc/[0-9]*; do n=$((n+1)); done; printf 'COUNT=%s\\n' \"$n\""],
            cwd=ROOT, capture_output=True, text=True, timeout=25,
        )
        assert ("Resource temporarily unavailable" in exceeded.stderr
                or exceeded.returncode != 0), exceeded.stderr[-500:]
        count = next(line for line in exceeded.stdout.splitlines() if line.startswith("COUNT="))
        assert int(count.split("=", 1)[1]) <= limit, count
    finally:
        runtime._docker(["docker", "rm", "-f", name])


def test_no_leaked_containers(runtime):
    leftovers = _cli(["docker", "ps", "-aq", "--filter", "name=dbcas-broker-"])
    assert leftovers == ""
