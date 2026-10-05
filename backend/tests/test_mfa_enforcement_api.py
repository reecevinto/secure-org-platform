from datetime import UTC, datetime

import pyotp
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.mfa_security import encrypt_mfa_secret
from app.models.mfa_credential import MFACredential
from app.models.session import Session as AuthSession
from app.models.user import User

PASSWORD = "CorrectHorseBatteryStaple!"


def create_mfa_enabled_user(
    db: Session,
    email: str,
    secret: str,
) -> User:
    from app.core.security import hash_password

    user = User(
        email=email,
        password_hash=hash_password(PASSWORD),
        first_name="MFA",
        last_name="Enforced",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    credential = MFACredential(
        user_id=user.id,
        type="totp",
        secret_reference=encrypt_mfa_secret(secret),
        enabled_at=datetime.now(UTC),
    )

    db.add(credential)
    db.commit()

    return user


def cleanup_user(db: Session, user: User) -> None:
    db.execute(
        delete(AuthSession).where(
            AuthSession.user_id == user.id,
        )
    )
    db.execute(
        delete(MFACredential).where(
            MFACredential.user_id == user.id,
        )
    )
    db.delete(user)
    db.commit()


def test_mfa_enabled_login_requires_second_factor(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, db = integration_client

    secret = pyotp.random_base32()

    user = create_mfa_enabled_user(
        db=db,
        email=f"mfa-enforced-{datetime.now(UTC).timestamp()}@example.com",
        secret=secret,
    )

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": user.email,
                "password": PASSWORD,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["mfa_required"] is True
        assert data["mfa_challenge"]

        assert "session_identifier" not in data
        assert "session-identifier" not in response.headers

        persisted_session = db.scalar(
            select(AuthSession).where(
                AuthSession.user_id == user.id,
            )
        )

        assert persisted_session is None
    finally:
        cleanup_user(db, user)


def test_mfa_enabled_login_rejects_invalid_totp_without_session(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, db = integration_client

    secret = pyotp.random_base32()

    user = create_mfa_enabled_user(
        db=db,
        email=f"mfa-invalid-{datetime.now(UTC).timestamp()}@example.com",
        secret=secret,
    )

    try:
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": user.email,
                "password": PASSWORD,
            },
        )

        challenge = login_response.json()["mfa_challenge"]

        verify_response = client.post(
            "/api/v1/auth/mfa/verify",
            json={
                "challenge": challenge,
                "code": "000000",
            },
        )

        assert verify_response.status_code == 401
        assert "session-identifier" not in verify_response.headers

        persisted_session = db.scalar(
            select(AuthSession).where(
                AuthSession.user_id == user.id,
            )
        )

        assert persisted_session is None
    finally:
        cleanup_user(db, user)


def test_mfa_enabled_login_creates_session_after_valid_totp(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, db = integration_client

    secret = pyotp.random_base32()

    user = create_mfa_enabled_user(
        db=db,
        email=f"mfa-valid-{datetime.now(UTC).timestamp()}@example.com",
        secret=secret,
    )

    try:
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": user.email,
                "password": PASSWORD,
            },
        )

        assert login_response.status_code == 200

        challenge = login_response.json()["mfa_challenge"]

        code = pyotp.TOTP(secret).now()

        verify_response = client.post(
            "/api/v1/auth/mfa/verify",
            json={
                "challenge": challenge,
                "code": code,
            },
        )

        assert verify_response.status_code == 200
        assert verify_response.json() == {
            "message": "MFA verification successful.",
        }

        session_identifier = verify_response.headers.get(
            "session-identifier",
        )

        assert session_identifier

        persisted_session = db.scalar(
            select(AuthSession).where(
                AuthSession.session_identifier == session_identifier,
            )
        )

        assert persisted_session is not None
        assert persisted_session.user_id == user.id
    finally:
        cleanup_user(db, user)
