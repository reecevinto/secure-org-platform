from datetime import UTC, datetime
from uuid import UUID

import pyotp
from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from app.core.mfa_security import decrypt_mfa_secret, encrypt_mfa_secret
from app.core.totp import generate_totp_secret
from app.models.mfa_credential import MFACredential
from app.models.session import Session


def create_mfa_credential(
    db: DatabaseSession,
    user_id: UUID,
    credential_type: str,
    secret_reference: str,
) -> MFACredential:
    """Create and persist an MFA credential reference."""

    credential = MFACredential(
        user_id=user_id,
        type=credential_type,
        secret_reference=secret_reference,
    )

    db.add(credential)
    db.commit()
    db.refresh(credential)

    return credential


def enroll_totp_credential(
    db: DatabaseSession,
    session: Session,
) -> tuple[MFACredential, str]:
    """Create an encrypted, initially disabled TOTP credential."""

    secret = generate_totp_secret()
    encrypted_secret = encrypt_mfa_secret(secret)

    credential = create_mfa_credential(
        db=db,
        user_id=session.user_id,
        credential_type="totp",
        secret_reference=encrypted_secret,
    )

    return credential, secret


def get_mfa_credentials_for_user(
    db: DatabaseSession,
    user_id: UUID,
) -> list[MFACredential]:
    """Retrieve MFA credentials belonging to a user."""

    return list(
        db.scalars(
            select(MFACredential)
            .where(MFACredential.user_id == user_id)
            .order_by(MFACredential.created_at)
        )
    )


class MFAVerificationError(Exception):
    """Raised when MFA verification cannot be completed."""


def verify_totp_credential(
    db: DatabaseSession,
    session: Session,
    code: str,
) -> MFACredential:
    """Verify a user's TOTP code and record successful verification."""

    credentials = get_mfa_credentials_for_user(
        db=db,
        user_id=session.user_id,
    )

    totp_credentials = [
        credential for credential in credentials if credential.type == "totp"
    ]

    if not totp_credentials:
        raise MFAVerificationError("MFA verification failed.")

    verified_credential: MFACredential | None = None

    for credential in totp_credentials:
        try:
            secret = decrypt_mfa_secret(credential.secret_reference)
        except ValueError as exc:
            raise MFAVerificationError("MFA verification failed.") from exc

        if pyotp.TOTP(secret).verify(code):
            verified_credential = credential
            break

    if verified_credential is None:
        raise MFAVerificationError("MFA verification failed.")

    now = datetime.now(UTC)

    if verified_credential.enabled_at is None:
        verified_credential.enabled_at = now

    verified_credential.last_used_at = now

    db.commit()
    db.refresh(verified_credential)

    return verified_credential


def mark_mfa_credential_used(
    db: DatabaseSession,
    credential: MFACredential,
    used_at: datetime,
) -> MFACredential:
    """Record the most recent successful use of an MFA credential."""

    credential.last_used_at = used_at

    db.commit()
    db.refresh(credential)

    return credential
