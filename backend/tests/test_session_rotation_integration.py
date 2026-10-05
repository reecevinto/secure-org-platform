import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models.session import Session
from app.models.user import User
from app.services.session import create_session, rotate_session


def test_rotate_session_persists_replacement_and_revokes_original() -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()

    user = User(
        email=f"session-rotation-{uuid.uuid4()}@example.com",
        password_hash="integration-test-hash",
        first_name="Session",
        last_name="Rotation",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    expires_at = datetime.now(UTC) + timedelta(hours=1)

    original_session = create_session(
        db=db,
        user_id=user.id,
        expires_at=expires_at,
        ip_address="192.0.2.10",
        user_agent="SessionRotationIntegrationTest/1.0",
    )

    original_identifier = original_session.session_identifier

    try:
        replacement_session = rotate_session(
            db=db,
            session_identifier=original_identifier,
        )

        assert replacement_session is not None
        assert replacement_session.id != original_session.id
        assert replacement_session.session_identifier != original_identifier

        persisted_original = db.scalar(
            select(Session).where(Session.id == original_session.id)
        )

        persisted_replacement = db.scalar(
            select(Session).where(Session.id == replacement_session.id)
        )

        assert persisted_original is not None
        assert persisted_replacement is not None

        assert persisted_original.revoked_at is not None
        assert persisted_replacement.revoked_at is None

        assert persisted_replacement.user_id == user.id
        assert persisted_replacement.expires_at == expires_at

        assert persisted_replacement.ip_address == "192.0.2.10"
        assert persisted_replacement.user_agent == "SessionRotationIntegrationTest/1.0"
    finally:
        if "replacement_session" in locals():
            db.delete(replacement_session)

        db.delete(original_session)
        db.delete(user)
        db.commit()
        db.close()


def test_rotate_session_rejects_already_revoked_session_in_postgresql() -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()

    user = User(
        email=f"session-rotation-revoked-{uuid.uuid4()}@example.com",
        password_hash="integration-test-hash",
        first_name="Session",
        last_name="Rotation",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    expires_at = datetime.now(UTC) + timedelta(hours=1)

    original_session = create_session(
        db=db,
        user_id=user.id,
        expires_at=expires_at,
    )

    try:
        original_session.revoked_at = datetime.now(UTC)
        db.commit()
        db.refresh(original_session)

        result = rotate_session(
            db=db,
            session_identifier=original_session.session_identifier,
        )

        assert result is None

        persisted_session = db.scalar(
            select(Session).where(Session.id == original_session.id)
        )

        assert persisted_session is not None
        assert persisted_session.revoked_at is not None

        session_count = len(
            db.scalars(select(Session).where(Session.user_id == user.id)).all()
        )

        assert session_count == 1
    finally:
        db.delete(original_session)
        db.delete(user)
        db.commit()
        db.close()
