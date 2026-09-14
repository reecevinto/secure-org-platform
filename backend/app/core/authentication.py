from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DatabaseSession

from app.core.database import get_db
from app.models.session import Session
from app.services.session import get_session_by_identifier


def get_current_session(
    db: Annotated[DatabaseSession, Depends(get_db)],
    session_identifier: str | None = Header(default=None),
) -> Session:
    """Resolve the authenticated session from the request header."""

    if not session_identifier:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    session = get_session_by_identifier(
        db=db,
        session_identifier=session_identifier,
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication session.",
        )

    if session.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication session has been revoked.",
        )

    return session
