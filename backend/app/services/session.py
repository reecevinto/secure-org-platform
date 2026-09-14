from datetime import datetime

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
