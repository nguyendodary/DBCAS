"""Bounded readiness retries without real sleeps or Docker calls."""
from types import SimpleNamespace

import conftest
import pytest


@pytest.mark.parametrize("fail_first", [False, True])
def test_readiness_succeeds_without_unnecessary_delay(monkeypatch, capsys, fail_first):
    clock = [0.0]
    sleeps = []
    calls = []

    def sleep(seconds):
        sleeps.append(seconds)
        clock[0] += seconds

    def command(*args, timeout):
        calls.append((args, timeout))
        clock[0] += 0.25
        if fail_first and len(calls) == 1:
            raise RuntimeError("not ready")

    monkeypatch.setattr(conftest, "time", SimpleNamespace(monotonic=lambda: clock[0], sleep=sleep))
    monkeypatch.setattr(conftest, "shutil", SimpleNamespace(which=lambda _: "docker"))
    monkeypatch.setattr(conftest, "docker_command", command)

    assert conftest._docker_ok() is True
    assert len(calls) == (2 if fail_first else 1)
    assert all(args == ("info",) and 0 < timeout <= 15 for args, timeout in calls)
    assert sleeps == ([1] if fail_first else [])
    output = capsys.readouterr().err
    assert "attempt 1" in output and "succeeded" in output
    if fail_first:
        assert "attempt 1 failed" in output and "attempt 2 succeeded" in output


def test_readiness_failure_stops_at_deadline(monkeypatch, capsys):
    clock = [0.0]
    sleeps = []
    timeouts = []

    def sleep(seconds):
        sleeps.append(seconds)
        clock[0] += seconds

    def command(*args, timeout):
        assert args == ("info",)
        timeouts.append(timeout)
        clock[0] += timeout
        raise RuntimeError("daemon unavailable")

    monkeypatch.setattr(conftest, "time", SimpleNamespace(monotonic=lambda: clock[0], sleep=sleep))
    monkeypatch.setattr(conftest, "shutil", SimpleNamespace(which=lambda _: "docker"))
    monkeypatch.setattr(conftest, "docker_command", command)

    assert conftest._docker_ok() is False
    assert clock[0] == 60
    assert timeouts == [15, 15, 15, 8]
    assert sleeps == [1, 2, 4]
    output = capsys.readouterr().err
    assert output.count("failed after") == 4
    assert "attempt 4 failed" in output and "elapsed 60.0s" in output
