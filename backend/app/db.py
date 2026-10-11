from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from .config import get_settings


@lru_cache
def get_engine():
    settings = get_settings()
    return create_engine(
        settings.database_url, pool_pre_ping=True,
        pool_size=settings.database_pool_size, max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
        connect_args={"connect_timeout": settings.database_connect_timeout_seconds},
    )


def get_session_factory() -> sessionmaker:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one SQLAlchemy session per request."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def get_readiness_db() -> Iterator[Session]:
    """Probe a fresh connection with bounded connection and statement waits.

    Readiness must not depend on a stale application-pool connection. This
    statement deadline applies only to probes, not learner/admin transactions.
    libpq connection timeouts apply per resolved address/host.
    """
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={
            "connect_timeout": settings.readiness_database_timeout_seconds,
            "options": "-c statement_timeout=1000 -c lock_timeout=1000",
        },
    )
    try:
        with Session(engine, autoflush=False, expire_on_commit=False) as db:
            yield db
    finally:
        engine.dispose()
