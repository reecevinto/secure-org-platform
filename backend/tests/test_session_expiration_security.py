import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session as DatabaseSession

from app.core.authentication import get_current_session
from app.models.session import Session


def create_expired_session() -> Session:
    return Session(
        user_id=uuid.uuid4(),
        session_identifier="stolen-expired-session",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
        revoked_at=None,
        ip_address="203.0.113.50",
        user_agent="AttackerBrowser/1.0",
    )


def test_expired_stolen_session_cannot_authenticate() -> None:
    db = MagicMock(spec=DatabaseSession)
    session = create_expired_session()

    db.scalar.return_value = session

    with pytest.raises(HTTPException) as exc_info:
        get_current_session(
            db=db,
            session_identifier="stolen-expired-session",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == ("Authentication session has expired.")


def test_expired_session_is_rejected_even_when_not_revoked() -> None:
    db = MagicMock(spec=DatabaseSession)
    session = create_expired_session()

    assert session.revoked_at is None

    db.scalar.return_value = session

    with pytest.raises(HTTPException) as exc_info:
        get_current_session(
            db=db,
            session_identifier=session.session_identifier,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == ("Authentication session has expired.")


def test_expiration_cannot_be_bypassed_by_session_metadata() -> None:
    db = MagicMock(spec=DatabaseSession)
    session = create_expired_session()

    session.ip_address = None
    session.user_agent = None

    db.scalar.return_value = session

    with pytest.raises(HTTPException) as exc_info:
        get_current_session(
            db=db,
            session_identifier=session.session_identifier,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == ("Authentication session has expired.")


def test_expired_session_does_not_trigger_database_mutation() -> None:
    db = MagicMock(spec=DatabaseSession)
    session = create_expired_session()

    db.scalar.return_value = session

    with pytest.raises(HTTPException):
        get_current_session(
            db=db,
            session_identifier=session.session_identifier,
        )

    assert session.revoked_at is None
    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.flush.assert_not_called()
    db.delete.assert_not_called()


def test_expired_session_does_not_leak_session_details() -> None:
    db = MagicMock(spec=DatabaseSession)
    session = create_expired_session()

    db.scalar.return_value = session

    with pytest.raises(HTTPException) as exc_info:
        get_current_session(
            db=db,
            session_identifier=session.session_identifier,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == ("Authentication session has expired.")

    assert str(session.user_id) not in str(exc_info.value.detail)
    assert session.ip_address not in str(exc_info.value.detail)
    assert session.user_agent not in str(exc_info.value.detail)
