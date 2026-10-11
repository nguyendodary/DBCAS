from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


@lru_cache
def get_engine():
    settings = get_settings()
    return create_engine(
        settings.database_url, pool_pre_ping=True,
        pool_size=settings.database_pool_size, max_overflow=settings.database_max_overflow,
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
