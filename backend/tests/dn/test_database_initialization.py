"""Exercise DN initialization against isolated PostgreSQL 17 schemas."""
import uuid

import psycopg
import pytest

from app.config import get_settings
from app.init_db import initialize


def test_fresh_init_seed_repeat_and_refresh_constraints():
    namespace = "dn_init_" + uuid.uuid4().hex[:12]
    with psycopg.connect(get_settings().database_url.replace("postgresql+psycopg://", "postgresql://"), autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            assert initialize(conn, seed_development=True, deployment_mode="development")
            assert initialize(conn, seed_development=True, deployment_mode="development") == []
            account_id = conn.execute("SELECT account_id FROM account WHERE email='admin@dbcas.local'").fetchone()[0]
            assert conn.execute("SELECT count(*) FROM account").fetchone()[0] == 1
            assert conn.execute("SELECT count(*) FROM role").fetchone()[0] == 2
            with pytest.raises(psycopg.errors.CheckViolation):
                conn.execute("INSERT INTO refresh_session(token_hash,family_id,account_id,expires_at) VALUES (%s,%s,%s,NOW()+INTERVAL '1 day')", ("bad", "a" * 32, account_id))
            conn.execute("INSERT INTO refresh_session(token_hash,family_id,account_id,expires_at) VALUES (%s,%s,%s,NOW()+INTERVAL '1 day')", ("b" * 64, "a" * 32, account_id))
            assert conn.execute("SELECT count(*) FROM refresh_session").fetchone()[0] == 1
            with pytest.raises(ValueError, match="forbidden"):
                initialize(conn, seed_development=True, deployment_mode="production")
        finally:
            conn.execute("SET search_path TO public")
            conn.execute(f'DROP SCHEMA "{namespace}" CASCADE')


def test_initialization_refuses_unrelated_schema():
    namespace = "dn_init_" + uuid.uuid4().hex[:12]
    with psycopg.connect(get_settings().database_url.replace("postgresql+psycopg://", "postgresql://"), autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            conn.execute("CREATE TABLE unrelated(id int)")
            with pytest.raises(RuntimeError, match="not empty"):
                initialize(conn)
        finally:
            conn.execute("SET search_path TO public")
            conn.execute(f'DROP SCHEMA "{namespace}" CASCADE')
