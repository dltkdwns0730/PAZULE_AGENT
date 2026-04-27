import pytest
from sqlalchemy import text

from app.db.session import session_scope, smoke_check_database_connection


def test_smoke_check_database_connection_accepts_sqlite_url(tmp_path):
    database_path = tmp_path / "pazule-smoke.db"

    assert smoke_check_database_connection(f"sqlite:///{database_path}") is True


def test_session_scope_commits_on_success(tmp_path):
    database_path = tmp_path / "pazule-session.db"
    database_url = f"sqlite:///{database_path}"

    with session_scope(database_url) as session:
        session.execute(text("CREATE TABLE smoke_items (name TEXT NOT NULL)"))
        session.execute(text("INSERT INTO smoke_items (name) VALUES ('committed')"))

    with session_scope(database_url) as session:
        result = session.execute(text("SELECT name FROM smoke_items")).scalar_one()

    assert result == "committed"


def test_session_scope_rolls_back_on_error(tmp_path):
    database_path = tmp_path / "pazule-rollback.db"
    database_url = f"sqlite:///{database_path}"

    with session_scope(database_url) as session:
        session.execute(text("CREATE TABLE smoke_items (name TEXT NOT NULL)"))

    with pytest.raises(RuntimeError):
        with session_scope(database_url) as session:
            session.execute(
                text("INSERT INTO smoke_items (name) VALUES ('rolled_back')")
            )
            raise RuntimeError("force rollback")

    with session_scope(database_url) as session:
        count = session.execute(text("SELECT COUNT(*) FROM smoke_items")).scalar_one()

    assert count == 0
