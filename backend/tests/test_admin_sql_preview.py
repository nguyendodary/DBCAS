"""Preview safety contracts, independent of the application's database fixtures.

Run: python -m pytest --noconftest tests/test_admin_sql_preview.py
"""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.deps import get_current_account, get_sandbox_runner
from app.errors import AppError, register_exception_handlers
from app.routers.admin import router
from app.schemas import AdminSqlPreviewRequest
from app.services.admin_sql_preview import preview_sql
from app.services.sandbox_runner import SandboxError, SandboxResult

SETUP = 'CREATE TABLE sample (amount int); INSERT INTO sample VALUES (0);'


def runner():
    fake = Mock()
    fake.provision_dataset.return_value = 'ds_test'
    fake.execute.return_value = SandboxResult(success=True, columns=['amount'], rows=[[0]], row_count=1)
    return fake


def test_preview_returns_actual_output_and_always_cleans_up():
    fake = runner()
    result = preview_sql(AdminSqlPreviewRequest(sql='SELECT amount FROM sample', setup_sql=SETUP), fake)
    assert result.success and result.rows == [[0]]
    fake.execute.assert_called_once_with('SELECT amount FROM sample', schema='ds_test')
    fake.drop_dataset.assert_called_once_with('ds_test')


@pytest.mark.parametrize('query', ['DELETE FROM sample', 'SELECT 1; DROP TABLE sample',
                                  'SELECT pg_read_file(\'/etc/passwd\')', 'SELECT * FROM pg_catalog.pg_authid'])
def test_unsafe_answers_are_rejected_before_provisioning(query):
    fake = runner()
    result = preview_sql(AdminSqlPreviewRequest(sql=query, setup_sql=SETUP), fake)
    assert not result.success
    fake.provision_dataset.assert_not_called()


def test_execution_failure_still_cleans_up():
    fake = runner()
    fake.execute.side_effect = SandboxError('sandbox_unavailable', 'Sandbox unavailable')
    with pytest.raises(AppError) as error:
        preview_sql(AdminSqlPreviewRequest(sql='SELECT 1', setup_sql=SETUP), fake)
    assert error.value.status_code == 503
    fake.drop_dataset.assert_called_once_with('ds_test')


def test_query_errors_are_returned_without_success_claim():
    fake = runner()
    fake.execute.return_value = SandboxResult(success=False, error_type='schema_error', error_message='Column not found')
    result = preview_sql(AdminSqlPreviewRequest(sql='SELECT missing FROM sample', setup_sql=SETUP), fake)
    assert not result.success and result.error_type == 'schema_error'
    fake.drop_dataset.assert_called_once()


def test_invalid_setup_is_a_controlled_error():
    fake = runner()
    fake.provision_dataset.side_effect = SandboxError('dataset_setup_failed', 'Invalid setup')
    with pytest.raises(AppError) as error:
        preview_sql(AdminSqlPreviewRequest(sql='SELECT 1', setup_sql='DROP TABLE account'), fake)
    assert error.value.status_code == 422
    fake.execute.assert_not_called()


def test_multibyte_payload_limit_is_enforced():
    with pytest.raises(ValidationError):
        AdminSqlPreviewRequest(sql='SELECT 1', setup_sql='\u1ea1' * 23000)


@pytest.mark.parametrize('role,status', [('Learner', 403), ('Administrator', 200), (None, 401)])
def test_preview_endpoint_requires_admin(role, status):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix='/api/v1')
    fake = runner()
    def account():
        if role is None:
            raise AppError(401, 'missing_token', 'Sign in required')
        return SimpleNamespace(roles=[SimpleNamespace(role_name=role)])
    app.dependency_overrides[get_current_account] = account
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    app.dependency_overrides[get_sandbox_runner] = lambda: fake
    with TestClient(app) as client:
        response = client.post('/api/v1/admin/sql/preview', json={'sql': 'SELECT amount FROM sample', 'setup_sql': SETUP})
    assert response.status_code == status
    if status != 200:
        fake.provision_dataset.assert_not_called()
