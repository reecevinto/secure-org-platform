import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import UserLoginRequest, UserLoginResponse
from app.services.login import InvalidCredentialsError, login_user


def create_login_request() -> UserLoginRequest:
    return UserLoginRequest(
        email="  User@Example.COM  ",
        password="CorrectHorseBatteryStaple!",
    )


def create_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="user@example.com",
        password_hash="$argon2id$example-hash",
        first_name="Example",
        last_name="User",
        status="registered",
    )


def test_login_user_returns_safe_user_response() -> None:
    db = MagicMock(spec=Session)
    user = create_user()
    db.scalar.return_value = user

    request = create_login_request()

    with patch("app.services.login.verify_password", return_value=True):
        response = login_user(db, request)

    assert isinstance(response, UserLoginResponse)
    assert response.email == "user@example.com"
    assert response.first_name == "Example"
    assert response.last_name == "User"
    assert response.status == "registered"
    assert not hasattr(response, "password")
    assert not hasattr(response, "password_hash")


def test_login_user_normalizes_email_before_lookup() -> None:
    db = MagicMock(spec=Session)
    user = create_user()
    db.scalar.return_value = user

    request = create_login_request()

    with patch("app.services.login.verify_password", return_value=True):
        login_user(db, request)

    statement = db.scalar.call_args.args[0]

    assert statement.compile().params["email_1"] == "user@example.com"


def test_login_user_rejects_incorrect_password() -> None:
    db = MagicMock(spec=Session)
    db.scalar.return_value = create_user()

    request = create_login_request()

    with (
        patch("app.services.login.verify_password", return_value=False),
        pytest.raises(InvalidCredentialsError) as exc_info,
    ):
        login_user(db, request)

    assert str(exc_info.value) == "Invalid email or password."


def test_login_user_rejects_unknown_email() -> None:
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    request = create_login_request()

    with pytest.raises(InvalidCredentialsError) as exc_info:
        login_user(db, request)

    assert str(exc_info.value) == "Invalid email or password."


def test_login_user_does_not_expose_password_hash() -> None:
    db = MagicMock(spec=Session)
    db.scalar.return_value = create_user()

    request = create_login_request()

    with patch("app.services.login.verify_password", return_value=True):
        response = login_user(db, request)

    response_data = response.model_dump()

    assert "password" not in response_data
    assert "password_hash" not in response_data
