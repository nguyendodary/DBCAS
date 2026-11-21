"""Unit tests for sandbox_busy rejection diagnostics; no Docker is used."""
import json
import logging

import pytest

from app.config import get_settings
from app.services import ephemeral_sandbox as module
from app.services.ephemeral_sandbox import EphemeralSandboxRunner
from app.services.sandbox_runner import SandboxError


class _BusySemaphore:
    def __init__(self, result=False):
        self.result = result
        self.calls = []

    def acquire(self, blocking=True, timeout=None):
        self.calls.append((blocking, timeout))
        return self.result

    def release(self):
        pass


@pytest.fixture()
def runner():
    settings = get_settings().model_copy(update={"sandbox_mode": "ephemeral"})
    return EphemeralSandboxRunner(settings)


def _busy(monkeypatch, result=False):
    slots = _BusySemaphore(result)
    monkeypatch.setattr(module, "_SLOTS", slots)
    return slots


def _rejection_message(records):
    messages = [record.getMessage() for record in records
                if "sandbox_busy rejection" in record.getMessage()]
    assert messages
    return messages[-1].split("sandbox_busy rejection ", 1)[1]


def test_rejection_behavior_unchanged(runner, monkeypatch):
    slots = _busy(monkeypatch, False)

    def forbidden(*args, **kwargs):
        raise AssertionError("Docker must not be called on a busy rejection")

    monkeypatch.setattr(runner, "_docker", forbidden)
    with pytest.raises(SandboxError) as exc:
        runner._create()
    assert exc.value.code == "sandbox_busy"
    assert exc.value.message == "SQL executor capacity is temporarily full"
    assert slots.calls == [(True, 5)]


def test_rejection_log_contains_diagnostic_fields(runner, monkeypatch, caplog):
    _busy(monkeypatch, False)
    with runner.diagnostics.operation_context("grading_submit"):
        runner.diagnostics.acquired()
        try:
            caplog.clear()
            with caplog.at_level(logging.WARNING):
                with pytest.raises(SandboxError):
                    runner._create()
            payload = json.loads(_rejection_message(caplog.records))
            assert payload["event"] == "sandbox_busy"
            assert isinstance(payload["worker_pid"], int) and payload["worker_pid"] > 0
            assert payload["slot_count"] == 2
            assert payload["available_slots"] == 1
            assert payload["wait_ms"] >= 0
            assert payload["operation"] == "grading_submit"
            holders = payload["active_holders"]
            assert holders and holders[0]["purpose"] == "grading_submit"
            assert holders[0]["held_ms"] >= 0
            record = [item for item in caplog.records
                      if "sandbox_busy rejection" in item.getMessage()][-1]
            assert record.sd_worker_pid == payload["worker_pid"]
            assert record.sd_slot_count == 2
            assert record.sd_available_slots == 1
            assert record.sd_operation == "grading_submit"
            assert record.sd_active_holders[0]["purpose"] == "grading_submit"
        finally:
            runner.diagnostics.released()


def test_rejection_log_has_no_sensitive_data(runner, monkeypatch, caplog):
    _busy(monkeypatch, False)
    sensitive = "SELECT secret_column FROM private_table WHERE token='learner-42'"
    with runner.diagnostics.operation_context("user_sql_run"):
        runner.diagnostics.acquired()
        try:
            caplog.clear()
            with caplog.at_level(logging.WARNING):
                with pytest.raises(SandboxError):
                    runner._create()
            text = "\n".join(record.getMessage() for record in caplog.records)
            assert sensitive not in text
            assert "learner-42" not in text
            assert "secret_column" not in text
            payload = json.loads(_rejection_message(caplog.records))
            assert payload["active_holders"][0]["purpose"] == "user_sql_run"
            assert all(set(holder) == {"purpose", "held_ms"}
                       for holder in payload["active_holders"])
        finally:
            runner.diagnostics.released()


def test_maintenance_grading_is_labelled_and_released(runner, monkeypatch):
    _busy(monkeypatch, True)
    with runner.grading_capacity() as admitted:
        assert admitted is True
        payload = runner.diagnostics.rejection(0)
        assert payload["active_holders"][0]["purpose"] == "grading_maintenance"
        assert payload["available_slots"] == 1
    assert runner.diagnostics.rejection(0)["active_holders"] == []
