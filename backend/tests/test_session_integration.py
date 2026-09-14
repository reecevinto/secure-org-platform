from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models.session import Session
from app.models.user import User
from app.services.session import create_session


def test_create_session_persists_to_postgresql() -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()

    user = User(
        email=f"session-integration-{datetime.now(UTC).timestamp()}@example.com",
        password_hash="integration-test-hash",
        first_name="Session",
        last_name="Integration",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    expires_at = datetime.now(UTC) + timedelta(hours=1)

    try:
        session = create_session(
            db=db,
            user_id=user.id,
            expires_at=expires_at,
            ip_address="192.0.2.10",
            user_agent="SessionIntegrationTest/1.0",
        )

        persisted_session = db.scalar(select(Session).where(Session.id == session.id))

        assert persisted_session is not None
        assert persisted_session.user_id == user.id
        assert persisted_session.session_identifier
        assert persisted_session.expires_at == expires_at
        assert persisted_session.ip_address == "192.0.2.10"
        assert persisted_session.user_agent == "SessionIntegrationTest/1.0"
        assert persisted_session.revoked_at is None
    finally:
        db.delete(session)
        db.delete(user)
        db.commit()
        db.close()


def test_session_requires_existing_user() -> None:
    from sqlalchemy.exc import IntegrityError

    from app.core.database import SessionLocal

    db = SessionLocal()

    try:
        nonexistent_user_id = __import__("uuid").uuid4()

        expires_at = datetime.now(UTC) + timedelta(hours=1)

        try:
            create_session(
                db=db,
                user_id=nonexistent_user_id,
                expires_at=expires_at,
            )
        except IntegrityError:
            db.rollback()
        else:
            raise AssertionError(
                "Expected PostgreSQL foreign-key constraint to reject "
                "a session for a nonexistent user."
            )
    finally:
        db.close()
