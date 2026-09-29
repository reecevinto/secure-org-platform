from datetime import UTC, datetime, timedelta

import pyotp
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.mfa_security import encrypt_mfa_secret
from app.models.mfa_credential import MFACredential
from app.models.user import User
from app.services.session import create_session


def test_mfa_verification_requires_authentication(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, _ = integration_client

    response = client.post(
        "/api/v1/auth/mfa/verify",
        json={"code": "123456"},
    )

    assert response.status_code == 401


def test_mfa_verification_rejects_invalid_session(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, _ = integration_client

    response = client.post(
        "/api/v1/auth/mfa/verify",
        headers={"session-identifier": "invalid-session"},
        json={"code": "123456"},
    )

    assert response.status_code == 401


def test_mfa_verification_rejects_revoked_session(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, db = integration_client

    user = User(
        email=f"mfa-revoked-{datetime.now(UTC).timestamp()}@example.com",
        password_hash="integration-test-hash",
        first_name="MFA",
        last_name="Revoked",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    session = create_session(
        db=db,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        ip_address="192.0.2.21",
        user_agent="MFAVerificationAPITest/1.0",
    )

    try:
        session.revoked_at = datetime.now(UTC)
        db.commit()

        response = client.post(
            "/api/v1/auth/mfa/verify",
            headers={
                "session-identifier": session.session_identifier,
            },
            json={"code": "123456"},
        )

        assert response.status_code == 401
    finally:
        db.delete(session)
        db.delete(user)
        db.commit()


def test_mfa_verification_accepts_valid_totp(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, db = integration_client

    user = User(
        email=f"mfa-valid-{datetime.now(UTC).timestamp()}@example.com",
        password_hash="integration-test-hash",
        first_name="MFA",
        last_name="Valid",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    session = create_session(
        db=db,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        ip_address="192.0.2.22",
        user_agent="MFAVerificationAPITest/1.0",
    )

    secret = pyotp.random_base32()

    credential = MFACredential(
        user_id=user.id,
        type="totp",
        secret_reference=encrypt_mfa_secret(secret),
    )

    db.add(credential)
    db.commit()
    db.refresh(credential)

    try:
        code = pyotp.TOTP(secret).now()

        response = client.post(
            "/api/v1/auth/mfa/verify",
            headers={
                "session-identifier": session.session_identifier,
            },
            json={"code": code},
        )

        assert response.status_code == 200
        assert response.json() == {
            "message": "MFA verification successful.",
        }

        db.refresh(credential)

        assert credential.enabled_at is not None
        assert credential.last_used_at is not None
    finally:
        db.delete(credential)
        db.delete(session)
        db.delete(user)
        db.commit()


def test_mfa_verification_rejects_invalid_totp(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, db = integration_client

    user = User(
        email=f"mfa-invalid-{datetime.now(UTC).timestamp()}@example.com",
        password_hash="integration-test-hash",
        first_name="MFA",
        last_name="Invalid",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    session = create_session(
        db=db,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        ip_address="192.0.2.23",
        user_agent="MFAVerificationAPITest/1.0",
    )

    secret = pyotp.random_base32()

    credential = MFACredential(
        user_id=user.id,
        type="totp",
        secret_reference=encrypt_mfa_secret(secret),
    )

    db.add(credential)
    db.commit()
    db.refresh(credential)

    try:
        response = client.post(
            "/api/v1/auth/mfa/verify",
            headers={
                "session-identifier": session.session_identifier,
            },
            json={"code": "000000"},
        )

        assert response.status_code == 401

        db.refresh(credential)

        assert credential.enabled_at is None
        assert credential.last_used_at is None
    finally:
        db.delete(credential)
        db.delete(session)
        db.delete(user)
        db.commit()


def test_user_cannot_verify_another_users_totp(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, db = integration_client

    user_a = User(
        email=f"mfa-user-a-{datetime.now(UTC).timestamp()}@example.com",
        password_hash="integration-test-hash",
        first_name="MFA",
        last_name="UserA",
        status="registered",
    )

    db.add(user_a)
    db.commit()
    db.refresh(user_a)

    session_a = create_session(
        db=db,
        user_id=user_a.id,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        ip_address="192.0.2.24",
        user_agent="MFAVerificationAPITest/1.0",
    )

    user_b = User(
        email=f"mfa-user-b-{datetime.now(UTC).timestamp()}@example.com",
        password_hash="integration-test-hash",
        first_name="MFA",
        last_name="UserB",
        status="registered",
    )

    db.add(user_b)
    db.commit()
    db.refresh(user_b)

    session_b = create_session(
        db=db,
        user_id=user_b.id,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        ip_address="192.0.2.25",
        user_agent="MFAVerificationAPITest/1.0",
    )

    user_b_secret = pyotp.random_base32()

    user_b_credential = MFACredential(
        user_id=user_b.id,
        type="totp",
        secret_reference=encrypt_mfa_secret(user_b_secret),
    )

    db.add(user_b_credential)
    db.commit()
    db.refresh(user_b_credential)

    try:
        user_b_code = pyotp.TOTP(user_b_secret).now()

        response = client.post(
            "/api/v1/auth/mfa/verify",
            headers={
                "session-identifier": session_a.session_identifier,
            },
            json={"code": user_b_code},
        )

        assert response.status_code == 401

        db.refresh(user_b_credential)

        assert user_b_credential.enabled_at is None
        assert user_b_credential.last_used_at is None
    finally:
        db.delete(user_b_credential)
        db.delete(session_b)
        db.delete(user_b)
        db.delete(session_a)
        db.delete(user_a)
        db.commit()


def test_mfa_secret_is_not_returned_in_verification_response(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, db = integration_client

    user = User(
        email=f"mfa-secret-{datetime.now(UTC).timestamp()}@example.com",
        password_hash="integration-test-hash",
        first_name="MFA",
        last_name="Secret",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    session = create_session(
        db=db,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        ip_address="192.0.2.26",
        user_agent="MFAVerificationAPITest/1.0",
    )

    secret = pyotp.random_base32()
    encrypted_secret = encrypt_mfa_secret(secret)

    credential = MFACredential(
        user_id=user.id,
        type="totp",
        secret_reference=encrypted_secret,
    )

    db.add(credential)
    db.commit()
    db.refresh(credential)

    try:
        code = pyotp.TOTP(secret).now()

        response = client.post(
            "/api/v1/auth/mfa/verify",
            headers={
                "session-identifier": session.session_identifier,
            },
            json={"code": code},
        )

        assert response.status_code == 200

        response_text = response.text

        assert secret not in response_text
        assert encrypted_secret not in response_text
        assert code not in response_text
    finally:
        db.delete(credential)
        db.delete(session)
        db.delete(user)
        db.commit()


def test_successful_mfa_verification_persists_enabled_at(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, db = integration_client

    user = User(
        email=f"mfa-enabled-{datetime.now(UTC).timestamp()}@example.com",
        password_hash="integration-test-hash",
        first_name="MFA",
        last_name="Enabled",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    session = create_session(
        db=db,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        ip_address="192.0.2.27",
        user_agent="MFAVerificationAPITest/1.0",
    )

    secret = pyotp.random_base32()

    credential = MFACredential(
        user_id=user.id,
        type="totp",
        secret_reference=encrypt_mfa_secret(secret),
    )

    db.add(credential)
    db.commit()
    db.refresh(credential)

    try:
        assert credential.enabled_at is None

        code = pyotp.TOTP(secret).now()

        response = client.post(
            "/api/v1/auth/mfa/verify",
            headers={
                "session-identifier": session.session_identifier,
            },
            json={"code": code},
        )

        assert response.status_code == 200

        db.expire_all()

        persisted_credential = db.scalar(
            select(MFACredential).where(
                MFACredential.id == credential.id,
            )
        )

        assert persisted_credential is not None
        assert persisted_credential.enabled_at is not None
    finally:
        db.delete(credential)
        db.delete(session)
        db.delete(user)
        db.commit()


def test_successful_mfa_verification_persists_last_used_at(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, db = integration_client

    user = User(
        email=f"mfa-last-used-{datetime.now(UTC).timestamp()}@example.com",
        password_hash="integration-test-hash",
        first_name="MFA",
        last_name="LastUsed",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    session = create_session(
        db=db,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        ip_address="192.0.2.28",
        user_agent="MFAVerificationAPITest/1.0",
    )

    secret = pyotp.random_base32()

    credential = MFACredential(
        user_id=user.id,
        type="totp",
        secret_reference=encrypt_mfa_secret(secret),
    )

    db.add(credential)
    db.commit()
    db.refresh(credential)

    try:
        before_verification = datetime.now(UTC)

        code = pyotp.TOTP(secret).now()

        response = client.post(
            "/api/v1/auth/mfa/verify",
            headers={
                "session-identifier": session.session_identifier,
            },
            json={"code": code},
        )

        after_verification = datetime.now(UTC)

        assert response.status_code == 200

        db.expire_all()

        persisted_credential = db.scalar(
            select(MFACredential).where(
                MFACredential.id == credential.id,
            )
        )

        assert persisted_credential is not None
        assert persisted_credential.last_used_at is not None
        assert (
            before_verification
            <= persisted_credential.last_used_at
            <= after_verification
        )
    finally:
        db.delete(credential)
        db.delete(session)
        db.delete(user)
        db.commit()
