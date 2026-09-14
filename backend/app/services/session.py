from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from app.core.session_security import generate_session_identifier
from app.models.session import Session


def create_session(
    db: DatabaseSession,
    user_id,
    expires_at: datetime,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Session:
    """Create and persist a new authenticated user session."""

    session = Session(
        user_id=user_id,
        session_identifier=generate_session_identifier(),
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def get_session_by_identifier(
    db: DatabaseSession,
    session_identifier: str,
) -> Session | None:
    """Retrieve a session by its session identifier."""

    return db.scalar(
        select(Session).where(Session.session_identifier == session_identifier)
    )


def revoke_session(
    db: DatabaseSession,
    session_identifier: str,
) -> Session | None:
    """Revoke an existing session without deleting it."""

    session = get_session_by_identifier(
        db=db,
        session_identifier=session_identifier,
    )

    if session is None:
        return None

    if session.revoked_at is None:
        session.revoked_at = datetime.now(UTC)
        db.commit()
        db.refresh(session)

    return session
