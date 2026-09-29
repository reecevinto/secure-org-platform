from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pyotp
import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.mfa_security import encrypt_mfa_secret
from app.models.mfa_credential import MFACredential
from app.models.session import Session as AuthSession
from app.models.user import User
from app.services.mfa import (
    MFAVerificationError,
    verify_totp_credential,
)


def create_test_user(db: Session) -> User:
    user = User(
        email=f"mfa-verification-{uuid4()}@example.com",
        password_hash="test-password-hash",
        first_name="MFA",
        last_name="Verification",
        status="active",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_test_session(
    db: Session,
    user: User,
) -> AuthSession:
    session = AuthSession(
        user_id=user.id,
        session_identifier=f"session-{uuid4()}",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def create_totp_credential(
    db: Session,
    user: User,
    secret: str,
) -> MFACredential:
    credential = MFACredential(
        user_id=user.id,
        type="totp",
        secret_reference=encrypt_mfa_secret(secret),
    )

    db.add(credential)
    db.commit()
    db.refresh(credential)

    return credential


def cleanup_test_data(
    db: Session,
    user_ids: list[UUID],
) -> None:
    for user_id in user_ids:
        db.execute(delete(AuthSession).where(AuthSession.user_id == user_id))
        db.execute(delete(MFACredential).where(MFACredential.user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))

    db.commit()


def test_valid_totp_verification_enables_credential(
    db: Session,
) -> None:
    user = create_test_user(db)
    session = create_test_session(db, user)

    secret = pyotp.random_base32()
    credential = create_totp_credential(db, user, secret)

    code = pyotp.TOTP(secret).now()

    try:
        result = verify_totp_credential(
            db=db,
            session=session,
            code=code,
        )

        assert result.id == credential.id
        assert result.enabled_at is not None
        assert result.last_used_at is not None
    finally:
        cleanup_test_data(db, [user.id])


def test_invalid_totp_does_not_enable_credential(
    db: Session,
) -> None:
    user = create_test_user(db)
    session = create_test_session(db, user)

    secret = pyotp.random_base32()
    credential = create_totp_credential(db, user, secret)

    try:
        with pytest.raises(MFAVerificationError):
            verify_totp_credential(
                db=db,
                session=session,
                code="000000",
            )

        db.refresh(credential)

        assert credential.enabled_at is None
        assert credential.last_used_at is None
    finally:
        cleanup_test_data(db, [user.id])


def test_subsequent_valid_verification_preserves_enabled_at(
    db: Session,
) -> None:
    user = create_test_user(db)
    session = create_test_session(db, user)

    secret = pyotp.random_base32()
    create_totp_credential(db, user, secret)

    try:
        first_code = pyotp.TOTP(secret).now()

        first_result = verify_totp_credential(
            db=db,
            session=session,
            code=first_code,
        )

        original_enabled_at = first_result.enabled_at

        assert original_enabled_at is not None
        assert first_result.last_used_at is not None

        second_code = pyotp.TOTP(secret).now()

        second_result = verify_totp_credential(
            db=db,
            session=session,
            code=second_code,
        )

        assert second_result.enabled_at == original_enabled_at
        assert second_result.last_used_at is not None
    finally:
        cleanup_test_data(db, [user.id])


def test_user_cannot_verify_another_users_totp(
    db: Session,
) -> None:
    user_a = create_test_user(db)
    user_b = create_test_user(db)

    session_a = create_test_session(db, user_a)

    secret_b = pyotp.random_base32()
    credential_b = create_totp_credential(db, user_b, secret_b)

    code_b = pyotp.TOTP(secret_b).now()

    try:
        with pytest.raises(MFAVerificationError):
            verify_totp_credential(
                db=db,
                session=session_a,
                code=code_b,
            )

        db.refresh(credential_b)

        assert credential_b.enabled_at is None
        assert credential_b.last_used_at is None
    finally:
        cleanup_test_data(db, [user_a.id, user_b.id])


def test_non_totp_credentials_are_not_used(
    db: Session,
) -> None:
    user = create_test_user(db)
    session = create_test_session(db, user)

    credential = MFACredential(
        user_id=user.id,
        type="webauthn",
        secret_reference="not-a-totp-secret",
    )

    db.add(credential)
    db.commit()
    db.refresh(credential)

    try:
        with pytest.raises(MFAVerificationError):
            verify_totp_credential(
                db=db,
                session=session,
                code="123456",
            )

        db.refresh(credential)

        assert credential.enabled_at is None
        assert credential.last_used_at is None
    finally:
        cleanup_test_data(db, [user.id])
