import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.models.session import Session
from app.services.session import create_session


def test_create_session_persists_session() -> None:
    db = MagicMock()
    user_id = uuid.uuid4()
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    with patch(
        "app.services.session.generate_session_identifier",
        return_value="secure-session-token",
    ):
        session = create_session(
            db=db,
            user_id=user_id,
            expires_at=expires_at,
        )

    assert isinstance(session, Session)
    assert session.user_id == user_id
    assert session.session_identifier == "secure-session-token"
    assert session.expires_at == expires_at

    db.add.assert_called_once_with(session)
    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(session)


def test_create_session_preserves_client_metadata() -> None:
    db = MagicMock()
    user_id = uuid.uuid4()
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    with patch(
        "app.services.session.generate_session_identifier",
        return_value="secure-session-token",
    ):
        session = create_session(
            db=db,
            user_id=user_id,
            expires_at=expires_at,
            ip_address="192.0.2.10",
            user_agent="TestClient/1.0",
        )

    assert session.ip_address == "192.0.2.10"
    assert session.user_agent == "TestClient/1.0"


def test_create_session_generates_identifier_internally() -> None:
    db = MagicMock()
    user_id = uuid.uuid4()
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    with patch(
        "app.services.session.generate_session_identifier",
        return_value="generated-token",
    ) as generate_identifier:
        session = create_session(
            db=db,
            user_id=user_id,
            expires_at=expires_at,
        )

    generate_identifier.assert_called_once_with()
    assert session.session_identifier == "generated-token"


def test_create_session_does_not_accept_caller_session_identifier() -> None:
    db = MagicMock()
    user_id = uuid.uuid4()
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    with patch(
        "app.services.session.generate_session_identifier",
        return_value="generated-token",
    ):
        session = create_session(
            db=db,
            user_id=user_id,
            expires_at=expires_at,
        )

    assert session.session_identifier == "generated-token"
    assert session.session_identifier != str(user_id)
