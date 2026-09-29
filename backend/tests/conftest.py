import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.main import app


@pytest.fixture
def db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def integration_client(
    db: Session,
) -> Generator[tuple[TestClient, Session]]:
    def override_get_db() -> Generator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield TestClient(app), db
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def unique_test_email() -> str:
    return f"integration-{uuid.uuid4()}@example.com"
