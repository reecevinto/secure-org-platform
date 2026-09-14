import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session as DatabaseSession

from app.models.mfa_credential import MFACredential
from app.models.session import Session
from app.services.mfa import enroll_totp_credential


def create_active_session() -> Session:
    return Session(
        user_id=uuid.uuid4(),
        session_identifier="valid-session",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )


def test_enroll_totp_credential_uses_authenticated_user() -> None:
    db = MagicMock(spec=DatabaseSession)
    session = create_active_session()

    credential = MFACredential(
        user_id=session.user_id,
        type="totp",
        secret_reference="encrypted-secret",
    )

    with (
        patch(
            "app.services.mfa.generate_totp_secret",
            return_value="JBSWY3DPEHPK3PXP",
        ),
        patch(
            "app.services.mfa.encrypt_mfa_secret",
            return_value="encrypted-secret",
        ),
        patch(
            "app.services.mfa.create_mfa_credential",
            return_value=credential,
        ) as create_credential,
    ):
        result_credential, secret = enroll_totp_credential(
            db=db,
            session=session,
        )

    assert result_credential is credential
    assert secret == "JBSWY3DPEHPK3PXP"

    create_credential.assert_called_once_with(
        db=db,
        user_id=session.user_id,
        credential_type="totp",
        secret_reference="encrypted-secret",
    )


def test_enroll_totp_credential_does_not_enable_mfa() -> None:
    db = MagicMock(spec=DatabaseSession)
    session = create_active_session()

    credential = MFACredential(
        user_id=session.user_id,
        type="totp",
        secret_reference="encrypted-secret",
    )

    with (
        patch(
            "app.services.mfa.generate_totp_secret",
            return_value="JBSWY3DPEHPK3PXP",
        ),
        patch(
            "app.services.mfa.encrypt_mfa_secret",
            return_value="encrypted-secret",
        ),
        patch(
            "app.services.mfa.create_mfa_credential",
            return_value=credential,
        ),
    ):
        result_credential, _ = enroll_totp_credential(
            db=db,
            session=session,
        )

    assert result_credential.enabled_at is None


def test_enroll_totp_credential_encrypts_generated_secret() -> None:
    db = MagicMock(spec=DatabaseSession)
    session = create_active_session()

    credential = MFACredential(
        user_id=session.user_id,
        type="totp",
        secret_reference="encrypted-secret",
    )

    with (
        patch(
            "app.services.mfa.generate_totp_secret",
            return_value="JBSWY3DPEHPK3PXP",
        ),
        patch(
            "app.services.mfa.encrypt_mfa_secret",
            return_value="encrypted-secret",
        ) as encrypt_secret,
        patch(
            "app.services.mfa.create_mfa_credential",
            return_value=credential,
        ),
    ):
        enroll_totp_credential(
            db=db,
            session=session,
        )

    encrypt_secret.assert_called_once_with("JBSWY3DPEHPK3PXP")
