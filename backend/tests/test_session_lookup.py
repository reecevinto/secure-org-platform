from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from app.models.session import Session
from app.services.session import get_session_by_identifier


def test_get_session_by_identifier_returns_matching_session() -> None:
    db = MagicMock()
    expected_session = Session(
        user_id=__import__("uuid").uuid4(),
        session_identifier="test-session-identifier",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    db.scalar.return_value = expected_session

    result = get_session_by_identifier(
        db=db,
        session_identifier="test-session-identifier",
    )

    assert result is expected_session
    db.scalar.assert_called_once()


def test_get_session_by_identifier_returns_none_when_not_found() -> None:
    db = MagicMock()
    db.scalar.return_value = None

    result = get_session_by_identifier(
        db=db,
        session_identifier="unknown-session-identifier",
    )

    assert result is None
    db.scalar.assert_called_once()
