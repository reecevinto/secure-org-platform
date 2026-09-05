from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import get_db


def test_get_db_provides_database_session() -> None:
    database = get_db()

    assert isinstance(database, Generator)

    session = next(database)

    assert isinstance(session, Session)

    database.close()
