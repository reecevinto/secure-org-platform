import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.session import Session
from app.models.user import User
from app.services.session import create_session, revoke_session


def test_revoke_session_persists_to_postgresql() -> None:
    db = SessionLocal()

    user = User(
        email=f"logout-integration-{uuid.uuid4()}@example.com",
        password_hash="integration-test-hash",
        first_name="Logout",
        last_name="Integration",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    session = None

    try:
        session = create_session(
            db=db,
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            ip_address="192.0.2.20",
            user_agent="LogoutIntegrationTest/1.0",
        )

        session_identifier = session.session_identifier

        revoked_session = revoke_session(
            db=db,
            session_identifier=session_identifier,
        )

        assert revoked_session is not None
        assert revoked_session.revoked_at is not None

        persisted_session = db.scalar(
            select(Session).where(Session.session_identifier == session_identifier)
        )

        assert persisted_session is not None
        assert persisted_session.id == session.id
        assert persisted_session.user_id == user.id
        assert persisted_session.revoked_at is not None

    finally:
        if session is not None:
            db.delete(session)

        db.delete(user)
        db.commit()
        db.close()


def test_revoke_session_preserves_original_revocation_timestamp_in_postgresql() -> None:
    db = SessionLocal()

    user = User(
        email=f"logout-repeat-{uuid.uuid4()}@example.com",
        password_hash="integration-test-hash",
        first_name="Logout",
        last_name="Repeat",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    session = None

    try:
        session = create_session(
            db=db,
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

        session_identifier = session.session_identifier

        first_revocation = revoke_session(
            db=db,
            session_identifier=session_identifier,
        )

        assert first_revocation is not None
        assert first_revocation.revoked_at is not None

        original_revoked_at = first_revocation.revoked_at

        second_revocation = revoke_session(
            db=db,
            session_identifier=session_identifier,
        )

        assert second_revocation is not None
        assert second_revocation.revoked_at == original_revoked_at

        persisted_session = db.scalar(
            select(Session).where(Session.session_identifier == session_identifier)
        )

        assert persisted_session is not None
        assert persisted_session.revoked_at == original_revoked_at

    finally:
        if session is not None:
            db.delete(session)

        db.delete(user)
        db.commit()
        db.close()


def test_revoke_unknown_session_does_not_modify_postgresql() -> None:
    db = SessionLocal()

    try:
        result = revoke_session(
            db=db,
            session_identifier=f"nonexistent-{uuid.uuid4()}",
        )

        assert result is None
    finally:
        db.close()
