from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from app.models.mfa_credential import MFACredential


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
