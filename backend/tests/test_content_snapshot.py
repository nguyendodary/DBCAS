import re
import uuid
import asyncio
from types import SimpleNamespace

import psycopg
from psycopg import sql
import pytest

from app import content_snapshot as snapshots
from app.config import ROOT_DIR, get_settings


@pytest.mark.parametrize('method,path,expected', [
    ('POST', '/api/v1/admin/questions', True),
    ('PUT', '/api/v1/admin/questions/1', True),
    ('DELETE', '/api/v1/admin/clos/2', True),
    ('PUT', '/api/v1/admin/concepts/3/prerequisites', True),
    ('POST', '/api/v1/admin/candidates/1/approve', True),
    ('GET', '/api/v1/admin/questions', False),
    ('POST', '/api/v1/auth/register', False),
    ('POST', '/api/v1/sessions/1/submit', False),
    ('PUT', '/api/v1/sessions/1/draft', False),
    ('PATCH', '/api/v1/admin/accounts/1', False),
    ('POST', '/api/v1/admin/sql/preview', False),
])
def test_only_shared_content_changes_trigger_export(method, path, expected):
    assert snapshots.content_mutation(method, path) is expected


def test_renderer_rejects_private_tables():
    with pytest.raises(ValueError):
        snapshots.render_snapshot({'account': [{'email': 'private@example.test'}]})
    assert not {'account', 'user_profile', 'attempt', 'assessment_session', 'oauth_handoff', 'grade_review'} & snapshots.CONTENT_COLUMNS.keys()
    assert all('created_by' not in columns for columns in snapshots.CONTENT_COLUMNS.values())


def test_failed_export_does_not_misreport_the_database_save(monkeypatch):
    def unavailable():
        raise OSError('Read-only content directory')
    monkeypatch.setattr(snapshots, 'export_snapshot', unavailable)
    assert snapshots.export_after_mutation() == 'failed'


@pytest.mark.parametrize('mode,path,expected', [
    ('development', '/api/v1/admin/questions', True),
    ('development', '/api/v1/sessions/1/submit', False),
    ('production', '/api/v1/admin/questions', False),
])
def test_response_exports_only_development_admin_content(monkeypatch, mode, path, expected):
    from app import main
    from starlette.responses import Response
    calls = []
    monkeypatch.setattr(main, 'settings', SimpleNamespace(deployment_mode=mode))
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising=False)
    monkeypatch.setattr(snapshots, 'export_after_mutation', lambda: calls.append(True) or 'saved')
    async def successful_save(request):
        return Response(status_code=201)
    response = asyncio.run(main.shared_admin_content(SimpleNamespace(method='POST', url=SimpleNamespace(path=path)), successful_save))
    assert bool(calls) is expected
    assert response.headers.get('X-DBCAS-Content-Snapshot') == ('saved' if expected else None)


def without_transaction_wrapper(value):
    return '\n'.join(line for line in value.splitlines() if line not in ('BEGIN;', 'COMMIT;'))


def test_real_snapshot_restores_content_without_learner_data_and_refuses_overwrite():
    """All test DDL/data live in a random schema and are rolled back."""
    source = snapshots.DEFAULT_PATH.read_text(encoding='utf-8')
    counts = {name: int(count) for name, count in re.findall(r'^-- (\w+): (\d+) rows$', source, re.M)}
    url = get_settings().database_url.replace('postgresql+psycopg://', 'postgresql://', 1)
    with psycopg.connect(url) as connection:
        try:
            namespace = 'content_snapshot_test_' + uuid.uuid4().hex[:12]
            connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(namespace)))
            connection.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(namespace)))
            connection.execute((ROOT_DIR / 'db/schema.sql').read_text(encoding='utf-8'), prepare=False)
            connection.execute((ROOT_DIR / 'db/seed.sql').read_text(encoding='utf-8'), prepare=False)
            connection.execute(without_transaction_wrapper(source), prepare=False)
            for table, count in counts.items():
                assert connection.execute(sql.SQL('SELECT COUNT(*) FROM {}').format(sql.Identifier(table))).fetchone()[0] == count
            assert connection.execute('SELECT count(*) FROM account').fetchone()[0] == 1
            assert connection.execute('SELECT count(*) FROM attempt').fetchone()[0] == 0
            assert connection.execute('SELECT count(*) FROM assessment_session').fetchone()[0] == 0
            maximum = connection.execute('SELECT max(question_id) FROM question').fetchone()[0]
            assert connection.execute("SELECT nextval(pg_get_serial_sequence('question', 'question_id'))").fetchone()[0] == (maximum + 1 if maximum else 1)
            if any(counts.values()):
                with pytest.raises(psycopg.errors.RaiseException, match='not empty'):
                    with connection.transaction():
                        connection.execute(without_transaction_wrapper(source), prepare=False)
                assert connection.execute('SELECT count(*) FROM question').fetchone()[0] == counts['question']
            # Exercise SQL quoting with user-authored apostrophes and SQL-like text.
            assert source.startswith('-- DBCAS shared Admin content.')
            assert 'INSERT INTO "account"' not in source
            assert 'INSERT INTO "attempt"' not in source
        finally:
            connection.rollback()
