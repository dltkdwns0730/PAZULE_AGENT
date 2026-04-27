"""SQLAlchemy engine and session helpers.

The current application still reads and writes JSON files for production
behavior. This module is the platform foundation for the DB-backed repository
migration that follows.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from app.core.config import settings


def get_database_url() -> str:
    """Return the configured database URL."""
    return settings.DATABASE_URL


def _require_sqlalchemy():
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "SQLAlchemy is not installed. Run `uv sync --dev` after the "
            "platform dependencies are added."
        ) from exc
    return create_engine, sessionmaker


def create_db_engine(database_url: str | None = None):
    """Create a SQLAlchemy Engine for the configured database."""
    create_engine, _ = _require_sqlalchemy()
    return create_engine(database_url or get_database_url(), future=True)


def create_session_factory(database_url: str | None = None):
    """Create a SQLAlchemy Session factory."""
    _, sessionmaker = _require_sqlalchemy()
    return sessionmaker(
        bind=create_db_engine(database_url), autoflush=False, future=True
    )


@contextmanager
def session_scope(database_url: str | None = None) -> Iterator[object]:
    """Yield a database session and commit or rollback around the block."""
    factory = create_session_factory(database_url)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def smoke_check_database_connection(database_url: str | None = None) -> bool:
    """Run a minimal SQL query to verify the configured DB connection."""
    try:
        from sqlalchemy import text
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "SQLAlchemy is not installed. Run `uv sync --dev` before DB checks."
        ) from exc

    engine = create_db_engine(database_url)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar_one()
    engine.dispose()
    return result == 1
