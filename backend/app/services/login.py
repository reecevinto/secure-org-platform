from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth import UserLoginRequest, UserLoginResponse


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""


def login_user(
    db: Session,
    request: UserLoginRequest,
) -> UserLoginResponse:
    """Authenticate a user using their email address and password."""

    normalized_email = request.email.strip().lower()

    user = db.scalar(select(User).where(User.email == normalized_email))

    if user is None:
        raise InvalidCredentialsError("Invalid email or password.")

    if not verify_password(request.password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password.")

    return UserLoginResponse.model_validate(user)
