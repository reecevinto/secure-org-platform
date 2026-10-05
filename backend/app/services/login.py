from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.mfa_challenge import create_mfa_challenge
from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth import UserLoginRequest, UserLoginResponse
from app.services.mfa import is_mfa_enabled_for_user
from app.services.session import create_session


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""


def login_user(
    db: Session,
    request: UserLoginRequest,
) -> UserLoginResponse:
    """Authenticate a user and enforce MFA when enabled."""

    normalized_email = request.email.strip().lower()

    user = db.scalar(select(User).where(User.email == normalized_email))

    if user is None:
        raise InvalidCredentialsError("Invalid email or password.")

    if not verify_password(request.password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password.")

    response = UserLoginResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        status=user.status,
    )

    if is_mfa_enabled_for_user(
        db=db,
        user_id=user.id,
    ):
        return response.model_copy(
            update={
                "mfa_required": True,
                "mfa_challenge": create_mfa_challenge(user.id),
            }
        )

    expires_at = datetime.now(UTC) + timedelta(
        seconds=settings.session_lifetime_seconds,
    )

    session = create_session(
        db=db,
        user_id=user.id,
        expires_at=expires_at,
    )

    return response.model_copy(
        update={
            "session_identifier": session.session_identifier,
        }
    )
