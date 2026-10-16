from sqlalchemy.exc import OperationalError, ProgrammingError
import socket
import threading
import time
import pytest
from pydantic import ValidationError
from sqlalchemy import text
from app import db as database
from app.config import Settings, get_settings
from app.main import app
from app.deps import get_sandbox_runner
from app.services import readiness_service

def test_readiness_checks_real_schema_and_sandbox(client, sandbox_runner):
    app.dependency_overrides[get_sandbox_runner] = lambda: sandbox_runner
    try:
        response = client.get('/readiness')
        assert response.status_code == 200
        assert response.json() == {'status': 'ready', 'dependencies': {'database': True, 'sandbox': True}}
    finally:
        app.dependency_overrides.pop(get_sandbox_runner, None)

def test_database_failure_is_unready_without_exposing_connection_information(db_session, monkeypatch):
    def fail(_):
        raise OperationalError('private DSN', None, Exception('private connection details'))
    monkeypatch.setattr(readiness_service.ReadinessRepository, 'check_schema', fail)
    class Sandbox:
        def is_ready(self): return True
    assert readiness_service.dependency_status(db_session, Sandbox()) == {'database': False, 'sandbox': True}

def test_sandbox_failure_is_unready_while_liveness_stays_available(client):
    class Sandbox:
        def is_ready(self): return False
    app.dependency_overrides[get_sandbox_runner] = Sandbox
    try:
        assert client.get('/health').json() == {'status': 'ok'}
        result = client.get('/readiness')
        assert result.status_code == 503
        assert result.json() == {'status': 'not_ready', 'dependencies': {'database': True, 'sandbox': False}}
    finally:
        app.dependency_overrides.pop(get_sandbox_runner, None)

def test_missing_migration_is_not_reported_ready(db_session, monkeypatch):
    def fail(_):
        raise ProgrammingError('missing table', None, Exception('unapplied migration'))
    monkeypatch.setattr(readiness_service.ReadinessRepository, 'check_schema', fail)
    class Sandbox:
        def is_ready(self): return True
    assert not readiness_service.dependency_status(db_session, Sandbox())['database']


@pytest.mark.parametrize('field,value', [
    ('database_connect_timeout_seconds', 0),
    ('database_connect_timeout_seconds', 31),
    ('database_pool_timeout_seconds', 0),
    ('readiness_database_timeout_seconds', 0),
    ('readiness_database_timeout_seconds', 11),
])
def test_database_wait_configuration_rejects_unbounded_values(field, value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: value})


def test_readiness_connection_has_real_postgresql_statement_deadline():
    dependency = database.get_readiness_db()
    db = next(dependency)
    started = time.monotonic()
    try:
        with pytest.raises(OperationalError) as failure:
            db.execute(text('SELECT pg_sleep(3)'))
        assert failure.value.orig.sqlstate == '57014'
        assert time.monotonic() - started < 3
        db.rollback()
    finally:
        dependency.close()


def test_readiness_returns_safe_503_when_tcp_server_never_authenticates(client, monkeypatch):
    # A real accepted TCP connection that never speaks PostgreSQL exercises the
    # driver's connection deadline, rather than mocking an immediate exception.
    stop = threading.Event()
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen(1)
    listener.settimeout(0.2)
    port = listener.getsockname()[1]
    def serve():
        while not stop.is_set():
            try:
                connection, _ = listener.accept()
            except socket.timeout:
                continue
            with connection:
                stop.wait(8)
            return
    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    settings = get_settings().model_copy(update={
        'database_url': f'postgresql+psycopg://probe:private@127.0.0.1:{port}/probe',
        'readiness_database_timeout_seconds': 2,
    })
    monkeypatch.setattr(database, 'get_settings', lambda: settings)
    class Sandbox:
        def is_ready(self): return True
    app.dependency_overrides[get_sandbox_runner] = Sandbox
    started = time.monotonic()
    try:
        response = client.get('/readiness')
        assert response.status_code == 503
        assert response.json() == {'status': 'not_ready', 'dependencies': {'database': False, 'sandbox': True}}
        assert time.monotonic() - started < 6
        assert 'private' not in response.text and str(port) not in response.text
        assert client.get('/health').status_code == 200
    finally:
        app.dependency_overrides.pop(get_sandbox_runner, None)
        stop.set()
        thread.join(timeout=1)
        listener.close()
