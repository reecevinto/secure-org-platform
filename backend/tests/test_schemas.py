import pytest
from pydantic import ValidationError

from app.schemas.auth import UserRegistrationRequest


def test_registration_request_accepts_valid_data() -> None:
    request = UserRegistrationRequest(
        email="user@example.com",
        password="CorrectHorseBatteryStaple!",
        first_name="Example",
        last_name="User",
    )

    assert request.email == "user@example.com"
    assert request.password == "CorrectHorseBatteryStaple!"
    assert request.first_name == "Example"
    assert request.last_name == "User"


def test_registration_request_normalizes_email() -> None:
    request = UserRegistrationRequest(
        email="  User@Example.COM  ",
        password="CorrectHorseBatteryStaple!",
        first_name="Example",
        last_name="User",
    )

    assert request.email == "user@example.com"


def test_registration_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        UserRegistrationRequest(
            email="not-an-email",
            password="CorrectHorseBatteryStaple!",
            first_name="Example",
            last_name="User",
        )


def test_registration_request_requires_all_fields() -> None:
    with pytest.raises(ValidationError):
        UserRegistrationRequest(
            email="user@example.com",
            password="CorrectHorseBatteryStaple!",
            first_name="Example",
        )


def test_registration_request_does_not_accept_server_controlled_fields() -> None:
    request = UserRegistrationRequest(
        email="user@example.com",
        password="CorrectHorseBatteryStaple!",
        first_name="Example",
        last_name="User",
        status="active",
    )

    assert not hasattr(request, "status")
