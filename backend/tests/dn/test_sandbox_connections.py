"""Recover transient connection setup without replaying SQL or extending limits."""
import psycopg
import pytest

from app.config import get_settings
from app.services import sandbox_runner as module


class Connection:
    def __init__(self):
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def execute(self, statement, *args):
        self.statements.append(str(statement))
        return self

    def fetchone(self):
        return (1,)

    def rollback(self):
        pass

    def transaction(self):
        return self


def setup(monkeypatch, failures, budget=5):
    now, calls, connection = [0.0], [], Connection()
    def connect(*args, **kwargs):
        calls.append(kwargs["connect_timeout"])
        if len(calls) <= len(failures):
            error = failures[len(calls) - 1]
            now[0] += kwargs["connect_timeout"] if isinstance(error, psycopg.errors.ConnectionTimeout) else 0
            raise error
        return connection
    monkeypatch.setattr(module.psycopg, "connect", connect)
    monkeypatch.setattr(module.time, "monotonic", lambda: now[0])
    settings = get_settings().model_copy(update={"sandbox_connect_timeout_seconds": budget})
    return module.SandboxRunner(settings), calls, connection, now


def test_transient_connect_timeout_recovers_before_any_sql(monkeypatch):
    runner, calls, connection, now = setup(monkeypatch, [psycopg.errors.ConnectionTimeout("test timeout")])
    assert runner.is_ready() is True
    assert calls == [2, 3] and now[0] == 2
    assert connection.statements == ["BEGIN READ ONLY", "SELECT 1"]


def test_exhausted_connection_recovery_stays_inside_the_original_budget(monkeypatch):
    runner, calls, connection, now = setup(monkeypatch, [psycopg.errors.ConnectionTimeout("test timeout")] * 2)
    assert runner.is_ready() is False
    assert calls == [2, 3] and now[0] == 5 and connection.statements == []


def test_small_connection_budget_does_not_add_a_second_minimum_libpq_timeout(monkeypatch):
    runner, calls, connection, now = setup(monkeypatch, [psycopg.errors.ConnectionTimeout("test timeout")], budget=2)
    assert runner.is_ready() is False
    assert calls == [2] and now[0] == 2 and connection.statements == []


def test_authentication_failure_is_not_retried(monkeypatch):
    runner, calls, connection, _ = setup(monkeypatch, [psycopg.errors.InvalidPassword("test authentication failure")])
    assert runner.is_ready() is False
    assert len(calls) == 1 and connection.statements == []


def test_dataset_setup_executes_once_after_connection_recovery(monkeypatch):
    runner, calls, connection, _ = setup(monkeypatch, [psycopg.errors.ConnectionTimeout("test timeout")])
    assert runner.provision_dataset("CREATE TABLE t(id int); INSERT INTO t VALUES (1);").startswith("ds_")
    assert calls == [2, 3]
    assert sum(statement.startswith("CREATE TABLE") for statement in connection.statements) == 1
    assert sum(statement.startswith("INSERT INTO") for statement in connection.statements) == 1


def test_query_failure_never_retries_or_replays_a_statement(monkeypatch):
    runner, calls, connection, _ = setup(monkeypatch, [])
    def broken(*_):
        raise psycopg.errors.ConnectionTimeout("test query timeout")
    connection.execute = broken
    with pytest.raises(module.SandboxError):
        runner.provision_dataset("CREATE TABLE t(id int);")
    assert len(calls) == 1
