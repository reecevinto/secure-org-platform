import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.schemas.auth import UserRegistrationRequest, UserRegistrationResponse
from app.services.registration import (
    DuplicateUserError,
    register_user,
)


def create_registration_request() -> UserRegistrationRequest:
    return UserRegistrationRequest(
        email="  User@Example.COM  ",
        password="CorrectHorseBatteryStaple!",
        first_name="Example",
        last_name="User",
    )


def create_mock_db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    def refresh_user(user: object) -> None:
        user.id = uuid.uuid4()  # type: ignore[attr-defined]

    db.refresh.side_effect = refresh_user

    return db


def test_register_user_creates_registered_user() -> None:
    db = create_mock_db()

    request = create_registration_request()

    response = register_user(db, request)

    assert isinstance(response, UserRegistrationResponse)

    user = db.add.call_args.args[0]

    assert user.email == "user@example.com"
    assert user.first_name == "Example"
    assert user.last_name == "User"
    assert user.status == "registered"
    assert user.password_hash != request.password
    assert user.password_hash.startswith("$argon2id$")

    db.add.assert_called_once_with(user)
    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(user)


def test_register_user_does_not_persist_plaintext_password() -> None:
    db = create_mock_db()

    request = create_registration_request()

    register_user(db, request)

    user = db.add.call_args.args[0]

    assert user.password_hash != "CorrectHorseBatteryStaple!"
    assert "CorrectHorseBatteryStaple!" not in user.password_hash


def test_register_user_returns_safe_response() -> None:
    db = create_mock_db()

    request = create_registration_request()

    response = register_user(db, request)

    assert response.email == "user@example.com"
    assert response.first_name == "Example"
    assert response.last_name == "User"
    assert response.status == "registered"
    assert not hasattr(response, "password")
    assert not hasattr(response, "password_hash")


def test_register_user_rejects_existing_email() -> None:
    db = MagicMock(spec=Session)

    existing_user = MagicMock()
    db.scalar.return_value = existing_user

    request = create_registration_request()

    with pytest.raises(DuplicateUserError):
        register_user(db, request)

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_register_user_handles_database_uniqueness_race() -> None:
    db = MagicMock(spec=Session)
    db.scalar.return_value = None
    db.commit.side_effect = IntegrityError(
        "INSERT",
        {},
        Exception("duplicate key value violates unique constraint"),
    )

    request = create_registration_request()

    with pytest.raises(DuplicateUserError):
        register_user(db, request)

    db.rollback.assert_called_once_with()


def test_register_user_does_not_accept_server_controlled_fields() -> None:
    db = create_mock_db()

    request = UserRegistrationRequest(
        email="user@example.com",
        password="CorrectHorseBatteryStaple!",
        first_name="Example",
        last_name="User",
        status="active",
        password_hash="fake-hash",
    )

    register_user(db, request)

    user = db.add.call_args.args[0]

    assert user.status == "registered"
    assert user.password_hash != "fake-hash"
    assert user.password_hash.startswith("$argon2id$")
