"""Regressions for the Windows exec stream and the missing writable role."""
import os
from types import SimpleNamespace

import pytest

from app.config import get_settings
from app.services import ephemeral_sandbox as module
from app.services.sandbox_runner import SandboxError, SandboxRunner


@pytest.fixture()
def windows_probe(monkeypatch):
    monkeypatch.setattr(module.os, "name", "nt")
    monkeypatch.setattr(module.shutil, "which", lambda _: r"C:\docker\docker.EXE")
    monkeypatch.setattr(module, "_WSL_DOCKER", None)
    return monkeypatch


def test_docker_cli_prefers_wsl_when_its_docker_is_usable(windows_probe):
    windows_probe.setattr(module, "_wsl_docker_available", lambda: True)
    assert module.docker_cli() == ["wsl.exe", "-e", "docker"]
    # The decision is cached; one probe per process, not one per SQL statement.
    assert module.docker_cli() == ["wsl.exe", "-e", "docker"]


def test_docker_cli_falls_back_to_native_without_wsl(windows_probe):
    windows_probe.setattr(module, "_wsl_docker_available", lambda: False)
    assert module.docker_cli() == [r"C:\docker\docker.EXE"]


def test_docker_cli_keeps_cmd_wrapper_fallback(windows_probe):
    windows_probe.setattr(module.shutil, "which", lambda _: r"C:\docker\docker.CMD")
    windows_probe.setattr(module, "_wsl_docker_available", lambda: False)
    assert module.docker_cli() == ["wsl.exe", "-e", "docker"]


def test_writable_provision_names_the_missing_learner_rw_role(monkeypatch):
    class _Result:
        def fetchone(self):
            return None

    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, sql, *args):
            if "pg_roles" in sql:
                return _Result()
            raise AssertionError("grants must not run without the role")

    settings = get_settings().model_copy(update={"sandbox_writable": True})
    runner = SandboxRunner(settings)
    monkeypatch.setattr(runner, "_connect", lambda *a, **k: _Conn())
    with pytest.raises(SandboxError) as exc:
        runner.provision_dataset("CREATE TABLE t(id int);")
    assert exc.value.code == "dataset_setup_failed"
    assert "learner_rw" in exc.value.message
