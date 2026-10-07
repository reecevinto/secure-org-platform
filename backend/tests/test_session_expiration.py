import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session as DatabaseSession

from app.core.authentication import get_current_session
from app.models.session import Session


def create_session(
    expires_at: datetime,
    revoked_at: datetime | None = None,
) -> Session:
    return Session(
        user_id=uuid.uuid4(),
        session_identifier="test-session",
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


def test_get_current_session_accepts_unexpired_session() -> None:
    db = MagicMock(spec=DatabaseSession)

    session = create_session(
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    db.scalar.return_value = session

    result = get_current_session(
        db=db,
        session_identifier="test-session",
    )

    assert result is session


def test_get_current_session_rejects_expired_session() -> None:
    db = MagicMock(spec=DatabaseSession)

    session = create_session(
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    db.scalar.return_value = session

    with pytest.raises(HTTPException) as exc_info:
        get_current_session(
            db=db,
            session_identifier="test-session",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authentication session has expired."


def test_get_current_session_rejects_session_at_expiration_boundary() -> None:
    db = MagicMock(spec=DatabaseSession)

    expiration = datetime.now(UTC) - timedelta(microseconds=1)
    session = create_session(expires_at=expiration)
    db.scalar.return_value = session

    with pytest.raises(HTTPException) as exc_info:
        get_current_session(
            db=db,
            session_identifier="test-session",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authentication session has expired."


def test_expired_session_is_not_automatically_revoked() -> None:
    db = MagicMock(spec=DatabaseSession)

    session = create_session(
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    db.scalar.return_value = session

    with pytest.raises(HTTPException):
        get_current_session(
            db=db,
            session_identifier="test-session",
        )

    assert session.revoked_at is None
    db.commit.assert_not_called()
    db.flush.assert_not_called()
    db.delete.assert_not_called()


def test_revoked_expired_session_reports_revocation() -> None:
    db = MagicMock(spec=DatabaseSession)

    session = create_session(
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
        revoked_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    db.scalar.return_value = session

    with pytest.raises(HTTPException) as exc_info:
        get_current_session(
            db=db,
            session_identifier="test-session",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == ("Authentication session has been revoked.")


def test_expired_session_requires_aware_datetime() -> None:
    db = MagicMock(spec=DatabaseSession)

    session = create_session(
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    db.scalar.return_value = session

    with pytest.raises(HTTPException) as exc_info:
        get_current_session(
            db=db,
            session_identifier="test-session",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authentication session has expired."
