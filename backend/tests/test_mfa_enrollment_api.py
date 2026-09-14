from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.mfa_security import decrypt_mfa_secret
from app.models.mfa_credential import MFACredential
from app.models.session import Session as AuthSession
from app.models.user import User
from app.services.session import create_session, revoke_session


def test_mfa_enrollment_requires_authentication(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, _ = integration_client

    response = client.post("/api/v1/auth/mfa/enroll")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_mfa_enrollment_rejects_invalid_session(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, _ = integration_client

    response = client.post(
        "/api/v1/auth/mfa/enroll",
        headers={"session-identifier": "invalid-session"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication session."


def test_mfa_enrollment_rejects_revoked_session(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, db = integration_client

    user = User(
        email=f"mfa-revoked-{uuid4()}@example.com",
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
    )

    try:
        revoked_session = revoke_session(
            db=db,
            session_identifier=session.session_identifier,
        )

        assert revoked_session is not None
        assert revoked_session.revoked_at is not None

        response = client.post(
            "/api/v1/auth/mfa/enroll",
            headers={"session-identifier": session.session_identifier},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication session has been revoked."
    finally:
        db.delete(session)
        db.delete(user)
        db.commit()


def test_mfa_enrollment_creates_encrypted_credential_for_authenticated_user(
    integration_client: tuple[TestClient, Session],
) -> None:
    client, db = integration_client

    user = User(
        email=f"mfa-enrollment-{uuid4()}@example.com",
        password_hash="integration-test-hash",
        first_name="MFA",
        last_name="Enrollment",
        status="registered",
    )

    unrelated_user = User(
        email=f"mfa-unrelated-{uuid4()}@example.com",
        password_hash="integration-test-hash",
        first_name="Unrelated",
        last_name="User",
        status="registered",
    )

    db.add_all([user, unrelated_user])
    db.commit()
    db.refresh(user)
    db.refresh(unrelated_user)

    session = create_session(
        db=db,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    credential = None

    try:
        response = client.post(
            "/api/v1/auth/mfa/enroll",
            headers={"session-identifier": session.session_identifier},
        )

        assert response.status_code == 200

        response_data = response.json()

        assert response_data["type"] == "totp"
        assert response_data["secret"]
        assert response_data["secret"] != ""

        credential = db.scalar(
            select(MFACredential).where(
                MFACredential.user_id == user.id,
            )
        )

        assert credential is not None
        assert credential.user_id == user.id
        assert credential.user_id != unrelated_user.id
        assert credential.type == "totp"

        assert credential.secret_reference
        assert credential.secret_reference != response_data["secret"]

        decrypted_secret = decrypt_mfa_secret(
            credential.secret_reference,
        )

        assert decrypted_secret == response_data["secret"]

        assert credential.enabled_at is None
        assert credential.last_used_at is None

        persisted_session = db.scalar(
            select(AuthSession).where(
                AuthSession.id == session.id,
            )
        )

        assert persisted_session is not None
        assert persisted_session.user_id == user.id

    finally:
        if credential is not None:
            db.delete(credential)

        db.delete(session)
        db.delete(unrelated_user)
        db.delete(user)
        db.commit()
