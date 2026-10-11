from sqlalchemy.exc import OperationalError, ProgrammingError
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
