import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session as DatabaseSession

from app.core.authentication import get_current_session
from app.models.session import Session


def create_active_session() -> Session:
    return Session(
        user_id=uuid.uuid4(),
        session_identifier="valid-session",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )


def test_get_current_session_returns_active_session() -> None:
    db = MagicMock(spec=DatabaseSession)
    session = create_active_session()

    db.scalar.return_value = session

    result = get_current_session(
        db=db,
        session_identifier="valid-session",
    )

    assert result is session


def test_get_current_session_rejects_missing_identifier() -> None:
    db = MagicMock(spec=DatabaseSession)

    with pytest.raises(HTTPException) as exc_info:
        get_current_session(
            db=db,
            session_identifier=None,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authentication required."
    db.scalar.assert_not_called()


def test_get_current_session_rejects_unknown_identifier() -> None:
    db = MagicMock(spec=DatabaseSession)
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_session(
            db=db,
            session_identifier="unknown-session",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication session."


def test_get_current_session_rejects_revoked_session() -> None:
    db = MagicMock(spec=DatabaseSession)

    session = create_active_session()
    session.revoked_at = datetime.now(UTC)

    db.scalar.return_value = session

    with pytest.raises(HTTPException) as exc_info:
        get_current_session(
            db=db,
            session_identifier="valid-session",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == ("Authentication session has been revoked.")
