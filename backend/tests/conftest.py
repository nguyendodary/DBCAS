"""Test fixtures: a disposable PostgreSQL container with the real schema.

The tests run against the real db/schema.sql so ORM mappings and constraints
are verified for real. Requires Docker; the suite is skipped without it.

Note: pg_isready inside the container reports ready during the image's
init phase (its temporary bootstrap server). We wait for a TCP connection
from the host instead — that only works once the real server is up.
"""

import atexit
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "db" / "schema.sql"


def _docker_ok() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        subprocess.run(
            ["docker", "info"], capture_output=True, timeout=15, check=True
        )
        return True
    except Exception:
        return False


def _start_test_db() -> str:
    """Start postgres:17 on a random localhost port; returns a libpq DSN."""
    import psycopg

    name = f"dbcas-test-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        [
            "docker", "run", "-d", "--name", name,
            "-e", "POSTGRES_PASSWORD=test", "-e", "POSTGRES_DB=dbcas_test",
            "-p", "127.0.0.1:0:5432",
            "postgres:17",
        ],
        check=True, capture_output=True,
    )
    atexit.register(
        lambda: subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    )
    port = (
        subprocess.run(
            ["docker", "port", name, "5432/tcp"],
            check=True, capture_output=True, text=True,
        )
        .stdout.strip()
        .rsplit(":", 1)[-1]
    )
    # 127.0.0.1 not localhost — the ::1 lookup adds a multi-second delay here.
    dsn = f"postgresql://postgres:test@127.0.0.1:{port}/dbcas_test"
    # Host TCP only succeeds once the final server (not the init bootstrap) is up.
    for _ in range(90):
        try:
            psycopg.connect(dsn, connect_timeout=2).close()
            break
        except Exception:
            time.sleep(1)
    else:
        raise RuntimeError("test database did not become ready")
    subprocess.run(
        [
            "docker", "exec", "-i", name, "psql",
            "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "dbcas_test",
        ],
        stdin=open(SCHEMA, "rb"),
        check=True, capture_output=True,
    )
    return dsn


if _docker_ok():
    os.environ["DATABASE_URL"] = _start_test_db()
    os.environ["JWT_SECRET"] = "test-secret-not-for-production"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
    DOCKER_DB = True
else:
    DOCKER_DB = False

pytestmark = pytest.mark.skipif(not DOCKER_DB, reason="Docker is required")

from sqlalchemy import text  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import get_session_factory  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Role  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Every test starts with empty data tables and the two seeded roles."""
    db = get_session_factory()()
    try:
        for table in (
            "attempt", "assessment_session", "assessment_concept", "assessment",
            "mcq_option", "question_concept", "question",
            "account_role", "user_profile", "account", "role",
        ):
            db.execute(text(f"TRUNCATE {table} RESTART IDENTITY CASCADE"))
        db.add_all(
            [
                Role(role_name="Learner", description="test"),
                Role(role_name="Administrator", description="test"),
            ]
        )
        db.commit()
        yield
    finally:
        db.close()


@pytest.fixture()
def db_session():
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
