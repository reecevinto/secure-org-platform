import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.password_recovery_token import PasswordRecoveryToken
from app.models.session import Session as AuthSession
from app.models.user import User
from app.schemas.auth import PasswordRecoveryRequest, PasswordResetRequest
from app.services.password_recovery import (
    InvalidRecoveryTokenError,
    request_password_recovery,
    reset_password,
)


@pytest.fixture
def mock_db() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture
def user() -> MagicMock:
    account = MagicMock(spec=User)
    account.id = uuid.uuid4()
    account.email = "person@example.com"
    account.deleted_at = None
    return account


def make_token(
    *,
    token: str = "valid-test-token",
    expires_at: datetime | None = None,
    used_at: datetime | None = None,
    user_id: uuid.UUID | None = None,
) -> PasswordRecoveryToken:
    return PasswordRecoveryToken(
        user_id=user_id or uuid.uuid4(),
        token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
        expires_at=expires_at or datetime.now(UTC) + timedelta(minutes=10),
        used_at=used_at,
    )


def test_recovery_for_unknown_email_returns_generic_response(
    mock_db: MagicMock,
) -> None:
    mock_db.scalar.return_value = None

    response = request_password_recovery(
        mock_db,
        PasswordRecoveryRequest(email="unknown@example.com"),
    )

    assert "If an account matches that email address" in response.message
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_recovery_stores_only_token_hash_and_sends_raw_token(
    mock_db: MagicMock,
    user: MagicMock,
) -> None:
    mock_db.scalar.return_value = user
    captured_tokens: list[PasswordRecoveryToken] = []

    def capture_token(token_record: PasswordRecoveryToken) -> None:
        captured_tokens.append(token_record)

    mock_db.add.side_effect = capture_token

    with patch("app.services.password_recovery.send_recovery_email") as send_email:
        response = request_password_recovery(
            mock_db,
            PasswordRecoveryRequest(email=" PERSON@EXAMPLE.COM "),
        )

    assert response.message
    assert len(captured_tokens) == 1

    stored_token = captured_tokens[0]
    assert stored_token.user_id == user.id
    assert len(stored_token.token_hash) == 64
    assert stored_token.token_hash != send_email.call_args.kwargs["token"]
    assert (
        stored_token.token_hash
        == hashlib.sha256(
            send_email.call_args.kwargs["token"].encode("utf-8")
        ).hexdigest()
    )

    send_email.assert_called_once()
    assert send_email.call_args.kwargs["recipient"] == user.email
    mock_db.commit.assert_called_once()


def test_recovery_delivery_failure_invalidates_token(
    mock_db: MagicMock,
    user: MagicMock,
) -> None:
    from app.services.email_delivery import RecoveryEmailDeliveryError

    mock_db.scalar.return_value = user
    captured_tokens: list[PasswordRecoveryToken] = []
    mock_db.add.side_effect = captured_tokens.append

    with patch(
        "app.services.password_recovery.send_recovery_email",
        side_effect=RecoveryEmailDeliveryError("delivery failed"),
    ):
        response = request_password_recovery(
            mock_db,
            PasswordRecoveryRequest(email=user.email),
        )

    assert response.message
    assert len(captured_tokens) == 1
    assert captured_tokens[0].used_at is not None
    assert mock_db.commit.call_count == 2


def test_recovery_delivery_cleanup_failure_is_not_suppressed(
    mock_db: MagicMock,
    user: MagicMock,
) -> None:
    from sqlalchemy.exc import SQLAlchemyError

    from app.services.email_delivery import RecoveryEmailDeliveryError

    mock_db.scalar.return_value = user
    mock_db.commit.side_effect = [None, SQLAlchemyError("database failure")]

    with (
        patch(
            "app.services.password_recovery.send_recovery_email",
            side_effect=RecoveryEmailDeliveryError("delivery failed"),
        ),
        pytest.raises(SQLAlchemyError),
    ):
        request_password_recovery(
            mock_db,
            PasswordRecoveryRequest(email=user.email),
        )

    mock_db.rollback.assert_called_once()


def test_reset_password_updates_hash_and_revokes_active_sessions(
    mock_db: MagicMock,
) -> None:
    raw_token = "valid-test-token"
    token_record = make_token(token=raw_token)
    account = MagicMock(spec=User)
    account.id = token_record.user_id
    account.deleted_at = None
    account.password_hash = "old-hash"

    mock_db.scalar.side_effect = [token_record, account, token_record]

    with patch(
        "app.services.password_recovery.hash_password",
        return_value="new-argon2-hash",
    ) as hash_password:
        response = reset_password(
            mock_db,
            PasswordResetRequest(
                token=raw_token,
                new_password="A-strong-new-password-123!",
            ),
        )

    assert response.message == "Password reset successful."
    hash_password.assert_called_once_with("A-strong-new-password-123!")
    assert account.password_hash == "new-argon2-hash"
    assert token_record.used_at is not None
    assert mock_db.execute.call_count == 2
    mock_db.commit.assert_called_once()

    executed_tables = [
        call.args[0].table.name for call in mock_db.execute.call_args_list
    ]

    assert executed_tables == [
        PasswordRecoveryToken.__tablename__,
        AuthSession.__tablename__,
    ]


@pytest.mark.parametrize(
    "token_record",
    [
        None,
        make_token(expires_at=datetime.now(UTC) - timedelta(seconds=1)),
        make_token(used_at=datetime.now(UTC)),
    ],
    ids=["missing", "expired", "already-used"],
)
def test_reset_rejects_invalid_expired_or_used_tokens(
    mock_db: MagicMock,
    token_record: PasswordRecoveryToken | None,
) -> None:
    mock_db.scalar.return_value = token_record

    with pytest.raises(InvalidRecoveryTokenError):
        reset_password(
            mock_db,
            PasswordResetRequest(
                token="valid-test-token",
                new_password="A-strong-new-password-123!",
            ),
        )

    mock_db.rollback.assert_called_once()
    mock_db.commit.assert_not_called()


def test_reset_rejects_soft_deleted_user(mock_db: MagicMock) -> None:
    token_record = make_token()
    mock_db.scalar.side_effect = [token_record, None]

    with pytest.raises(InvalidRecoveryTokenError):
        reset_password(
            mock_db,
            PasswordResetRequest(
                token="valid-test-token",
                new_password="A-strong-new-password-123!",
            ),
        )

    mock_db.rollback.assert_called_once()
    mock_db.commit.assert_not_called()


def test_reset_database_failure_rolls_back(mock_db: MagicMock) -> None:
    token_record = make_token()
    account = MagicMock(spec=User)
    account.id = token_record.user_id
    account.deleted_at = None
    mock_db.scalar.side_effect = [token_record, account, token_record]
    mock_db.commit.side_effect = RuntimeError("simulated failure")

    with (
        patch(
            "app.services.password_recovery.hash_password",
            return_value="new-hash",
        ),
        pytest.raises(RuntimeError, match="simulated failure"),
    ):
        reset_password(
            mock_db,
            PasswordResetRequest(
                token="valid-test-token",
                new_password="A-strong-new-password-123!",
            ),
        )

    mock_db.rollback.assert_called_once()


def test_token_persistence_failure_rolls_back_without_sending_email(
    mock_db: MagicMock,
    user: MagicMock,
) -> None:
    from sqlalchemy.exc import SQLAlchemyError

    mock_db.scalar.return_value = user
    mock_db.commit.side_effect = SQLAlchemyError("database unavailable")

    with (
        patch("app.services.password_recovery.send_recovery_email") as send_email,
        pytest.raises(SQLAlchemyError),
    ):
        request_password_recovery(
            mock_db,
            PasswordRecoveryRequest(email=user.email),
        )

    mock_db.rollback.assert_called_once()
    send_email.assert_not_called()
