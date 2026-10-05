import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    MFAVerificationRequest,
    MFAVerificationResponse,
)


def test_mfa_verification_request_accepts_six_digit_code() -> None:
    request = MFAVerificationRequest(code="123456")

    assert request.code == "123456"


@pytest.mark.parametrize(
    "code",
    [
        "",
        "12345",
        "1234567",
        "abcdef",
        "12345a",
    ],
)
def test_mfa_verification_request_rejects_invalid_code(
    code: str,
) -> None:
    with pytest.raises(ValidationError):
        MFAVerificationRequest(code=code)


def test_mfa_verification_request_ignores_extra_fields() -> None:
    request = MFAVerificationRequest(
        code="123456",
        user_id="should-not-be-used",
    )

    assert request.code == "123456"
    assert "user_id" not in request.model_dump()


def test_mfa_verification_response_accepts_message() -> None:
    response = MFAVerificationResponse(
        message="MFA verification successful.",
    )

    assert response.message == "MFA verification successful."


def test_mfa_verification_response_rejects_secret() -> None:
    with pytest.raises(ValidationError):
        MFAVerificationResponse(
            message="MFA verification successful.",
            secret="should-not-be-returned",
        )


def test_mfa_verification_request_accepts_login_challenge() -> None:
    request = MFAVerificationRequest(
        code="123456",
        challenge="encrypted-mfa-challenge",
    )

    assert request.challenge == "encrypted-mfa-challenge"


def test_mfa_verification_request_ignores_client_user_id() -> None:
    request = MFAVerificationRequest(
        code="123456",
        challenge="encrypted-mfa-challenge",
        user_id="attacker-controlled-user-id",
    )

    assert request.challenge == "encrypted-mfa-challenge"
    assert "user_id" not in request.model_dump()
