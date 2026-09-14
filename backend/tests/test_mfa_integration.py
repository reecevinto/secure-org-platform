import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.models.mfa_credential import MFACredential
from app.models.user import User
from app.services.mfa import (
    create_mfa_credential,
    get_mfa_credentials_for_user,
    mark_mfa_credential_used,
)


def test_create_mfa_credential_persists_to_postgresql() -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()

    user = User(
        email=f"mfa-integration-{datetime.now(UTC).timestamp()}@example.com",
        password_hash="integration-test-hash",
        first_name="MFA",
        last_name="Integration",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    credential = None

    try:
        credential = create_mfa_credential(
            db=db,
            user_id=user.id,
            credential_type="totp",
            secret_reference="test-secret-reference-1",
        )

        persisted_credential = db.scalar(
            select(MFACredential).where(MFACredential.id == credential.id)
        )

        assert persisted_credential is not None
        assert persisted_credential.user_id == user.id
        assert persisted_credential.type == "totp"
        assert persisted_credential.secret_reference == "test-secret-reference-1"
        assert persisted_credential.enabled_at is None
        assert persisted_credential.last_used_at is None
        assert persisted_credential.created_at is not None
        assert persisted_credential.updated_at is not None
    finally:
        if credential is not None:
            db.delete(credential)
        db.delete(user)
        db.commit()
        db.close()


def test_user_can_have_multiple_mfa_credentials() -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()

    user = User(
        email=f"mfa-multiple-{datetime.now(UTC).timestamp()}@example.com",
        password_hash="integration-test-hash",
        first_name="MFA",
        last_name="Multiple",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    credentials = []

    try:
        first_credential = create_mfa_credential(
            db=db,
            user_id=user.id,
            credential_type="totp",
            secret_reference="test-secret-reference-1",
        )

        second_credential = create_mfa_credential(
            db=db,
            user_id=user.id,
            credential_type="webauthn",
            secret_reference="test-secret-reference-2",
        )

        credentials.extend([first_credential, second_credential])

        user_credentials = get_mfa_credentials_for_user(
            db=db,
            user_id=user.id,
        )

        assert len(user_credentials) == 2
        assert user_credentials[0].user_id == user.id
        assert user_credentials[1].user_id == user.id

        credential_types = {credential.type for credential in user_credentials}

        assert credential_types == {"totp", "webauthn"}

        secret_references = {
            credential.secret_reference for credential in user_credentials
        }

        assert secret_references == {
            "test-secret-reference-1",
            "test-secret-reference-2",
        }
    finally:
        for credential in credentials:
            db.delete(credential)

        db.delete(user)
        db.commit()
        db.close()


def test_mark_mfa_credential_used_persists_last_used_at() -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()

    user = User(
        email=f"mfa-used-{datetime.now(UTC).timestamp()}@example.com",
        password_hash="integration-test-hash",
        first_name="MFA",
        last_name="Used",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    credential = None

    try:
        credential = create_mfa_credential(
            db=db,
            user_id=user.id,
            credential_type="totp",
            secret_reference="test-secret-reference-used",
        )

        used_at = datetime.now(UTC)

        updated_credential = mark_mfa_credential_used(
            db=db,
            credential=credential,
            used_at=used_at,
        )

        assert updated_credential.last_used_at == used_at

        persisted_credential = db.scalar(
            select(MFACredential).where(MFACredential.id == credential.id)
        )

        assert persisted_credential is not None
        assert persisted_credential.last_used_at == used_at
    finally:
        if credential is not None:
            db.delete(credential)

        db.delete(user)
        db.commit()
        db.close()


def test_mfa_credential_requires_existing_user() -> None:
    from sqlalchemy.exc import IntegrityError

    from app.core.database import SessionLocal

    db = SessionLocal()

    try:
        nonexistent_user_id = uuid.uuid4()

        try:
            create_mfa_credential(
                db=db,
                user_id=nonexistent_user_id,
                credential_type="totp",
                secret_reference="test-secret-reference-invalid",
            )
        except IntegrityError:
            db.rollback()
        else:
            raise AssertionError(
                "Expected PostgreSQL foreign-key constraint to reject "
                "an MFA credential for a nonexistent user."
            )
    finally:
        db.close()
