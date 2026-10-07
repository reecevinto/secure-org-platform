import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.authentication import get_current_session
from app.core.database import SessionLocal
from app.models.session import Session
from app.models.user import User
from app.services.session import create_session


def test_expired_session_is_rejected_from_postgresql() -> None:
    db = SessionLocal()

    user = User(
        email=f"session-expiration-{uuid.uuid4()}@example.com",
        password_hash="integration-test-hash",
        first_name="Session",
        last_name="Expiration",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    expired_session = create_session(
        db=db,
        user_id=user.id,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
        ip_address="192.0.2.20",
        user_agent="SessionExpirationIntegrationTest/1.0",
    )

    try:
        with pytest.raises(HTTPException) as exc_info:
            get_current_session(
                db=db,
                session_identifier=expired_session.session_identifier,
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == ("Authentication session has expired.")

        persisted_session = db.scalar(
            select(Session).where(Session.id == expired_session.id)
        )

        assert persisted_session is not None
        assert persisted_session.revoked_at is None
    finally:
        db.delete(expired_session)
        db.delete(user)
        db.commit()
        db.close()


def test_unexpired_session_is_accepted_from_postgresql() -> None:
    db = SessionLocal()

    user = User(
        email=f"session-expiration-active-{uuid.uuid4()}@example.com",
        password_hash="integration-test-hash",
        first_name="Session",
        last_name="Expiration",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    active_session = create_session(
        db=db,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        ip_address="192.0.2.21",
        user_agent="SessionExpirationIntegrationTest/1.0",
    )

    try:
        result = get_current_session(
            db=db,
            session_identifier=active_session.session_identifier,
        )

        assert result.id == active_session.id
        assert result.user_id == user.id
        assert result.session_identifier == active_session.session_identifier
        assert result.revoked_at is None
        assert result.expires_at > datetime.now(UTC)
    finally:
        db.delete(active_session)
        db.delete(user)
        db.commit()
        db.close()


def test_expired_session_remains_unrevoked_in_postgresql() -> None:
    db = SessionLocal()

    user = User(
        email=f"session-expiration-state-{uuid.uuid4()}@example.com",
        password_hash="integration-test-hash",
        first_name="Session",
        last_name="Expiration",
        status="registered",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    expired_session = create_session(
        db=db,
        user_id=user.id,
        expires_at=datetime.now(UTC) - timedelta(minutes=5),
    )

    try:
        with pytest.raises(HTTPException):
            get_current_session(
                db=db,
                session_identifier=expired_session.session_identifier,
            )

        db.expire_all()

        persisted_session = db.scalar(
            select(Session).where(Session.id == expired_session.id)
        )

        assert persisted_session is not None
        assert persisted_session.revoked_at is None
    finally:
        db.delete(expired_session)
        db.delete(user)
        db.commit()
        db.close()
