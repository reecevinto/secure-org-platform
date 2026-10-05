import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.models.session import Session
from app.services.session import rotate_session


def test_rotation_never_reuses_existing_session_identifier() -> None:
    db = MagicMock()

    existing_session = Session(
        user_id=uuid.uuid4(),
        session_identifier="existing-session-token",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    db.scalar.return_value = existing_session

    with patch(
        "app.services.session.generate_session_identifier",
        return_value="fresh-session-token",
    ) as generate_identifier:
        replacement = rotate_session(
            db=db,
            session_identifier="existing-session-token",
        )

    assert replacement is not None
    assert replacement.session_identifier != existing_session.session_identifier
    generate_identifier.assert_called_once_with()


def test_rotation_preserves_session_user_identity() -> None:
    db = MagicMock()

    user_id = uuid.uuid4()

    existing_session = Session(
        user_id=user_id,
        session_identifier="existing-session-token",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    db.scalar.return_value = existing_session

    with patch(
        "app.services.session.generate_session_identifier",
        return_value="fresh-session-token",
    ):
        replacement = rotate_session(
            db=db,
            session_identifier="existing-session-token",
        )

    assert replacement is not None
    assert replacement.user_id == existing_session.user_id
    assert replacement.user_id == user_id


def test_rotation_does_not_extend_session_lifetime() -> None:
    db = MagicMock()

    original_expiration = datetime.now(UTC) + timedelta(minutes=15)

    existing_session = Session(
        user_id=uuid.uuid4(),
        session_identifier="existing-session-token",
        expires_at=original_expiration,
    )

    db.scalar.return_value = existing_session

    with patch(
        "app.services.session.generate_session_identifier",
        return_value="fresh-session-token",
    ):
        replacement = rotate_session(
            db=db,
            session_identifier="existing-session-token",
        )

    assert replacement is not None
    assert replacement.expires_at == original_expiration


def test_revoked_session_cannot_be_rotated_into_new_credentials() -> None:
    db = MagicMock()

    revoked_at = datetime.now(UTC) - timedelta(minutes=5)

    existing_session = Session(
        user_id=uuid.uuid4(),
        session_identifier="revoked-session-token",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        revoked_at=revoked_at,
    )

    db.scalar.return_value = existing_session

    with patch(
        "app.services.session.generate_session_identifier",
    ) as generate_identifier:
        replacement = rotate_session(
            db=db,
            session_identifier="revoked-session-token",
        )

    assert replacement is None
    generate_identifier.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_unknown_session_cannot_create_new_credentials() -> None:
    db = MagicMock()
    db.scalar.return_value = None

    with patch(
        "app.services.session.generate_session_identifier",
    ) as generate_identifier:
        replacement = rotate_session(
            db=db,
            session_identifier="unknown-session-token",
        )

    assert replacement is None
    generate_identifier.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_rotation_revokes_old_credential_before_successful_return() -> None:
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
    ):
        replacement = rotate_session(
            db=db,
            session_identifier="old-session-token",
        )

    assert replacement is not None
    assert existing_session.revoked_at is not None
    assert replacement.revoked_at is None
