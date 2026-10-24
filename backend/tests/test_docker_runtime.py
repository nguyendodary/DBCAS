"""Pure command/ownership tests; no Docker daemon or database required."""
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import docker_runtime


def inspected(label="owned", mounts=None):
    return SimpleNamespace(returncode=0, stdout=json.dumps([{
        "Config": {"Labels": {"dbcas.test-run": label}}, "Mounts": mounts or []
    }]).encode())


def test_cleanup_removes_only_owned_container_without_volume_flag(monkeypatch):
    run = Mock(side_effect=[inspected(), SimpleNamespace(returncode=0)])
    monkeypatch.setattr(subprocess, "run", run)
    docker_runtime.cleanup_owned("dbcas-test-owned", "owned")
    assert run.call_args_list[1].args[0] == ["docker", "rm", "-f", "dbcas-test-owned"]
    assert run.call_args_list[1].kwargs["timeout"] == 15


@pytest.mark.parametrize("row", [inspected("foreign"), inspected(mounts=[{"Type": "volume"}]), inspected(mounts=[{"Type": "bind"}])])
def test_cleanup_refuses_foreign_or_persistent_container(monkeypatch, row):
    run = Mock(return_value=row)
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(RuntimeError, match="Cleanup refused"):
        docker_runtime.cleanup_owned("dbcas-test-owned", "owned")
    assert run.call_count == 1


@pytest.mark.parametrize("detail", [
    b"No such object: absent",
    b"error: no such object: absent",
    b"Error response from daemon: No such container: absent",
    b"error: no such container: absent",
])
def test_missing_container_needs_no_removal(monkeypatch, detail):
    run = Mock(return_value=SimpleNamespace(returncode=1, stderr=detail))
    monkeypatch.setattr(subprocess, "run", run)
    docker_runtime.cleanup_owned("absent", "owned")
    assert run.call_count == 1


def test_daemon_connection_failure_is_not_reported_as_missing_container(monkeypatch):
    run=Mock(return_value=SimpleNamespace(returncode=1,stderr=b'Cannot connect: No such file or directory'))
    monkeypatch.setattr(subprocess,'run',run)
    with pytest.raises(RuntimeError,match='Cannot verify ownership'):
        docker_runtime.cleanup_owned('owned','owned')
    assert run.call_count==1


def test_docker_failure_preserves_stderr(monkeypatch):
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=subprocess.CalledProcessError(125, ["docker"], stderr=b"port allocation failed")))
    with pytest.raises(RuntimeError, match="Docker start failed.*125.*port allocation failed"):
        docker_runtime.docker_command("start", "owned")


def test_docker_timeout_is_bounded_and_not_retried(monkeypatch):
    run = Mock(side_effect=subprocess.TimeoutExpired(["docker"], 3))
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(RuntimeError, match="timed out after 3s"):
        docker_runtime.docker_command("info", timeout=3)
    assert run.call_count == 1


@pytest.mark.parametrize("failure_at", [1, 2])
def test_create_and_start_failures_already_have_cleanup_ownership(monkeypatch,tmp_path,failure_at):
    registered=Mock();monkeypatch.setattr(docker_runtime.atexit,'register',registered)
    calls=[]
    def command(*args):
        calls.append(args)
        assert registered.call_count==1
        assert json.loads(receipt.read_text())=={'run_id':'owned','containers':['dbcas-test-owned']}
        if len(calls)==failure_at:raise RuntimeError('daemon timeout')
    monkeypatch.setattr(docker_runtime,'docker_command',command)
    receipt=tmp_path/'ownership.json';owned=[]
    with pytest.raises(RuntimeError,match='daemon timeout'):
        docker_runtime.create_owned('dbcas-test-owned','owned',owned,receipt,['--name','dbcas-test-owned'])
    registered.assert_called_once_with(docker_runtime.cleanup_at_exit,'dbcas-test-owned','owned')
    assert owned==['dbcas-test-owned']
