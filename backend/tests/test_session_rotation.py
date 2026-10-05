import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models.session import Session
from app.services.session import rotate_session


def test_rotate_session_revokes_old_session_and_creates_replacement() -> None:
    db = MagicMock()

    user_id = uuid.uuid4()
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    existing_session = Session(
        user_id=user_id,
        session_identifier="old-session-token",
        expires_at=expires_at,
        ip_address="192.0.2.10",
        user_agent="TestClient/1.0",
    )

    db.scalar.return_value = existing_session

    with patch(
        "app.services.session.generate_session_identifier",
        return_value="new-session-token",
    ):
        replacement_session = rotate_session(
            db=db,
            session_identifier="old-session-token",
        )

    assert replacement_session is not None
    assert replacement_session is not existing_session

    assert existing_session.revoked_at is not None
    assert replacement_session.session_identifier == "new-session-token"

    db.add.assert_called_once_with(replacement_session)
    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(replacement_session)


def test_rotate_session_generates_new_identifier() -> None:
    db = MagicMock()

    existing_session = Session(
        user_id=uuid.uuid4(),
        session_identifier="old-session-token",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    db.scalar.return_value = existing_session

    with patch(
        "app.services.session.generate_session_identifier",
        return_value="new-session-token",
    ) as generate_identifier:
        replacement_session = rotate_session(
            db=db,
            session_identifier="old-session-token",
        )

    assert replacement_session is not None
    assert replacement_session.session_identifier == "new-session-token"
    assert replacement_session.session_identifier != (
        existing_session.session_identifier
    )

    generate_identifier.assert_called_once_with()


def test_rotate_session_preserves_user_ownership() -> None:
    db = MagicMock()

    user_id = uuid.uuid4()

    existing_session = Session(
        user_id=user_id,
        session_identifier="old-session-token",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    db.scalar.return_value = existing_session

    with patch(
        "app.services.session.generate_session_identifier",
        return_value="new-session-token",
    ):
        replacement_session = rotate_session(
            db=db,
            session_identifier="old-session-token",
        )

    assert replacement_session is not None
    assert replacement_session.user_id == user_id


def test_rotate_session_preserves_expiration() -> None:
    db = MagicMock()

    expires_at = datetime.now(UTC) + timedelta(minutes=47)

    existing_session = Session(
        user_id=uuid.uuid4(),
        session_identifier="old-session-token",
        expires_at=expires_at,
    )

    db.scalar.return_value = existing_session

    with patch(
        "app.services.session.generate_session_identifier",
        return_value="new-session-token",
    ):
        replacement_session = rotate_session(
            db=db,
            session_identifier="old-session-token",
        )

    assert replacement_session is not None
    assert replacement_session.expires_at == expires_at


def test_rotate_session_preserves_client_metadata() -> None:
    db = MagicMock()

    existing_session = Session(
        user_id=uuid.uuid4(),
        session_identifier="old-session-token",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        ip_address="192.0.2.10",
        user_agent="TestClient/1.0",
    )

    db.scalar.return_value = existing_session

    with patch(
        "app.services.session.generate_session_identifier",
        return_value="new-session-token",
    ):
        replacement_session = rotate_session(
            db=db,
            session_identifier="old-session-token",
        )

    assert replacement_session is not None
    assert replacement_session.ip_address == "192.0.2.10"
    assert replacement_session.user_agent == "TestClient/1.0"


def test_rotate_session_returns_none_for_unknown_identifier() -> None:
    db = MagicMock()
    db.scalar.return_value = None

    result = rotate_session(
        db=db,
        session_identifier="unknown-session-token",
    )

    assert result is None
    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.refresh.assert_not_called()
    db.rollback.assert_not_called()


def test_rotate_session_returns_none_for_revoked_session() -> None:
    db = MagicMock()

    revoked_at = datetime.now(UTC) - timedelta(minutes=10)

    existing_session = Session(
        user_id=uuid.uuid4(),
        session_identifier="revoked-session-token",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        revoked_at=revoked_at,
    )

    db.scalar.return_value = existing_session

    result = rotate_session(
        db=db,
        session_identifier="revoked-session-token",
    )

    assert result is None
    assert existing_session.revoked_at == revoked_at

    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.refresh.assert_not_called()
    db.rollback.assert_not_called()


def test_rotate_session_rolls_back_when_commit_fails() -> None:
    db = MagicMock()

    existing_session = Session(
        user_id=uuid.uuid4(),
        session_identifier="old-session-token",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    db.scalar.return_value = existing_session
    db.commit.side_effect = RuntimeError("database failure")

    with (
        patch(
            "app.services.session.generate_session_identifier",
            return_value="new-session-token",
        ),
        pytest.raises(RuntimeError, match="database failure"),
    ):
        rotate_session(
            db=db,
            session_identifier="old-session-token",
        )

    assert existing_session.revoked_at is not None
    db.add.assert_called_once()
    db.commit.assert_called_once_with()
    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()
