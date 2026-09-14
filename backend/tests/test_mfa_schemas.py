import pytest
from pydantic import ValidationError

from app.schemas.auth import MFAEnrollmentResponse


def test_mfa_enrollment_response_accepts_valid_data() -> None:
    response = MFAEnrollmentResponse(
        type="totp",
        secret="JBSWY3DPEHPK3PXP",
    )

    assert response.type == "totp"
    assert response.secret == "JBSWY3DPEHPK3PXP"


def test_mfa_enrollment_response_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        MFAEnrollmentResponse(
            type="totp",
            secret="JBSWY3DPEHPK3PXP",
            user_id="unexpected-user-id",
        )
