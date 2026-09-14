import uuid
from datetime import UTC, datetime

from app.models.mfa_credential import MFACredential


def test_mfa_credential_model_has_expected_table_name() -> None:
    assert MFACredential.__tablename__ == "mfa_credentials"


def test_mfa_credential_accepts_uuid_id() -> None:
    credential_id = uuid.uuid4()

    credential = MFACredential(
        id=credential_id,
        user_id=uuid.uuid4(),
        type="totp",
        secret_reference="secret-reference-1",
    )

    assert credential.id == credential_id


def test_mfa_credential_accepts_expected_fields() -> None:
    user_id = uuid.uuid4()

    credential = MFACredential(
        user_id=user_id,
        type="totp",
        secret_reference="secret-reference-1",
    )

    assert credential.user_id == user_id
    assert credential.type == "totp"
    assert credential.secret_reference == "secret-reference-1"
    assert credential.enabled_at is None
    assert credential.last_used_at is None


def test_mfa_credential_supports_enabled_and_last_used_timestamps() -> None:
    now = datetime.now(UTC)

    credential = MFACredential(
        user_id=uuid.uuid4(),
        type="totp",
        secret_reference="secret-reference-1",
        enabled_at=now,
        last_used_at=now,
    )

    assert credential.enabled_at == now
    assert credential.last_used_at == now
