import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from app.models.session import Session
from app.services.session import revoke_session


def test_revoke_session_sets_revoked_at() -> None:
    db = MagicMock()

    session = Session(
        user_id=uuid.uuid4(),
        session_identifier="active-session",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    db.scalar.return_value = session

    before = datetime.now(UTC)

    result = revoke_session(
        db=db,
        session_identifier="active-session",
    )

    after = datetime.now(UTC)

    assert result is session
    assert session.revoked_at is not None
    assert before <= session.revoked_at <= after
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(session)


def test_revoke_session_returns_none_for_unknown_identifier() -> None:
    db = MagicMock()
    db.scalar.return_value = None

    result = revoke_session(
        db=db,
        session_identifier="unknown-session",
    )

    assert result is None
    db.commit.assert_not_called()
    db.refresh.assert_not_called()


def test_revoke_session_does_not_overwrite_existing_revocation() -> None:
    db = MagicMock()

    original_revoked_at = datetime.now(UTC) - timedelta(minutes=10)

    session = Session(
        user_id=uuid.uuid4(),
        session_identifier="already-revoked-session",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        revoked_at=original_revoked_at,
    )

    db.scalar.return_value = session

    result = revoke_session(
        db=db,
        session_identifier="already-revoked-session",
    )

    assert result is session
    assert session.revoked_at == original_revoked_at
    db.commit.assert_not_called()
    db.refresh.assert_not_called()
