"""Portable development curriculum and question bank, without learner data.

Export is read-only. Restore is allowed only into an empty content catalog;
it never resets a database, creates accounts or replaces learner evidence.
"""
import argparse
import logging
import os
from pathlib import Path
import tempfile
import threading

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from sqlalchemy import select

from .config import ROOT_DIR, get_settings
from .db import get_engine
from .models import Base

DEFAULT_PATH = ROOT_DIR / 'db' / 'shared_content.sql'
_LOCK = threading.Lock()
_LOG = logging.getLogger(__name__)

# Explicit column allowlist: no accounts, identities, profiles, attempts,
# sessions, grades, AI requests, creator IDs or reviewer information.
CONTENT_COLUMNS = {
    'concept': ('concept_id', 'concept_code', 'concept_name', 'subject_area',
                'description', 'difficulty_level', 'sql_feature', 'keywords', 'learning_objectives'),
    'course_learning_outcome': ('clo_id', 'clo_code', 'title', 'description', 'status'),
    'question': ('question_id', 'question_type', 'prompt', 'reference_answer',
                 'difficulty_level', 'points', 'source', 'status', 'family_id',
                 'version_no', 'explanation', 'tags', 'source_refs'),
    'mcq_option': ('option_id', 'question_id', 'option_label', 'option_text', 'is_correct'),
    'sql_test_dataset': ('dataset_id', 'question_id', 'dataset_name', 'setup_sql', 'expected_result', 'is_edge_case'),
    'rubric': ('rubric_id', 'question_id', 'level_name', 'min_score', 'max_score', 'criteria'),
    'question_translation': ('question_id', 'locale', 'source_hash', 'prompt', 'explanation', 'option_texts', 'rubrics'),
    'clo_concept': ('clo_id', 'concept_id', 'mapping_source', 'status'),
    'question_concept': ('question_id', 'concept_id', 'tag_source', 'is_required', 'confirmed', 'review_status'),
    'concept_dependency': ('concept_id', 'prerequisite_concept_id'),
}
IDENTITIES = {
    'concept': 'concept_id', 'course_learning_outcome': 'clo_id', 'question': 'question_id',
    'mcq_option': 'option_id', 'sql_test_dataset': 'dataset_id', 'rubric': 'rubric_id',
}
_JSON_COLUMNS = {'source_refs', 'expected_result', 'option_texts', 'rubrics'}
_ADMIN = sql.SQL("""(SELECT a.account_id FROM account a
    JOIN account_role ar ON ar.account_id=a.account_id
    JOIN role r ON r.role_id=ar.role_id
    WHERE r.role_name='Administrator' AND a.status='active'
    ORDER BY a.account_id LIMIT 1)""")


def read_content(connection):
    content = {}
    for name, columns in CONTENT_COLUMNS.items():
        table = Base.metadata.tables[name]
        statement = select(*(table.c[column] for column in columns)).order_by(*table.primary_key.columns)
        content[name] = [dict(row) for row in connection.execute(statement).mappings()]
    return content


def render_snapshot(content):
    unknown = set(content) - set(CONTENT_COLUMNS)
    if unknown:
        raise ValueError('Snapshot contains a non-content table')
    lines = [
        '-- DBCAS shared Admin content. Commit this file with the project.',
        '-- Contains curriculum and questions only; no accounts or learner results.',
        '-- Restore only after schema.sql and seed.sql, into an empty content catalog.',
        'BEGIN;',
        "SET LOCAL standard_conforming_strings = on;",
        "SET LOCAL lock_timeout = '5s';",
    ]
    for name in CONTENT_COLUMNS:
        lines.append(sql.SQL('LOCK TABLE {} IN SHARE ROW EXCLUSIVE MODE;').format(sql.Identifier(name)).as_string())
    lines.append('DO $guard$ BEGIN')
    for name in CONTENT_COLUMNS:
        lines.append(sql.SQL("IF EXISTS (SELECT 1 FROM {}) THEN RAISE EXCEPTION 'Content catalog is not empty; restore cancelled'; END IF;").format(sql.Identifier(name)).as_string())
    lines += [
        "IF NOT EXISTS (SELECT 1 FROM account a JOIN account_role ar USING(account_id) JOIN role r USING(role_id) WHERE r.role_name='Administrator' AND a.status='active') THEN RAISE EXCEPTION 'An existing active administrator is required'; END IF;",
        'END $guard$;',
    ]
    for name, columns in CONTENT_COLUMNS.items():
        rows = content.get(name, [])
        lines.append(f'\n-- {name}: {len(rows)} rows')
        if not rows:
            continue
        owned = name in {'question', 'course_learning_outcome'}
        output_columns = (*columns, 'created_by') if owned else columns
        values = []
        for row in rows:
            cells = [sql.Literal(Jsonb(row[column]) if column in _JSON_COLUMNS and row[column] is not None else row[column]) for column in columns]
            if owned:
                cells.append(_ADMIN)
            values.append(sql.SQL('({})').format(sql.SQL(', ').join(cells)))
        # One statement also preserves self-referencing question families.
        statement = sql.SQL('INSERT INTO {} ({}) {} VALUES\n{};').format(
            sql.Identifier(name), sql.SQL(', ').join(map(sql.Identifier, output_columns)),
            sql.SQL('OVERRIDING SYSTEM VALUE' if name in IDENTITIES else ''),
            sql.SQL(',\n').join(values),
        )
        lines.append(statement.as_string())
    for name, primary_key in IDENTITIES.items():
        lines.append(sql.SQL("SELECT setval(pg_get_serial_sequence({}, {}), GREATEST(COALESCE((SELECT MAX({}) FROM {}), 0), 1), EXISTS(SELECT 1 FROM {}));").format(
            sql.Literal(name), sql.Literal(primary_key), sql.Identifier(primary_key),
            sql.Identifier(name), sql.Identifier(name),
        ).as_string())
    lines.append('COMMIT;\n')
    return '\n'.join(lines)


def export_snapshot(path=DEFAULT_PATH):
    if get_settings().deployment_mode != 'development':
        raise RuntimeError('Automatic shared content snapshots are for development only')
    path = Path(path)
    with _LOCK:
        with get_engine().connect().execution_options(isolation_level='REPEATABLE READ') as connection:
            with connection.begin():
                connection.exec_driver_sql('SET TRANSACTION READ ONLY')
                content = read_content(connection)
        output = render_snapshot(content)
        if not path.exists() or path.read_text(encoding='utf-8') != output:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=path.parent, prefix='.shared-content-', suffix='.tmp', delete=False) as handle:
                    temporary = handle.name
                    handle.write(output)
                os.replace(temporary, path)
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)
        return {name: len(rows) for name, rows in content.items()}


def content_mutation(method, path):
    if method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        return False
    return any(path == prefix or path.startswith(prefix + '/') for prefix in (
        '/api/v1/admin/concepts', '/api/v1/admin/clos', '/api/v1/admin/questions',
        '/api/v1/admin/candidates',
    ))


def export_after_mutation():
    try:
        export_snapshot()
        return 'saved'
    except Exception:
        _LOG.exception('Admin content was saved to the database, but its Git snapshot could not be updated; run python -m app.content_snapshot export')
        return 'failed'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('export', 'restore'))
    parser.add_argument('--file', type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    if get_settings().deployment_mode != 'development':
        parser.error('This helper is for development databases only')
    if args.action == 'export':
        print(export_snapshot(args.file))
    else:
        url = get_settings().database_url.replace('postgresql+psycopg://', 'postgresql://', 1)
        with psycopg.connect(url) as connection:
            connection.execute(args.file.read_text(encoding='utf-8'), prepare=False)
        print('Shared content restored; account and learner data were not imported.')


if __name__ == '__main__':
    main()
