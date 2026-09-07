from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.auth import UserRegistrationRequest, UserRegistrationResponse


class DuplicateUserError(Exception):
    """Raised when a registration uses an existing email address."""


def register_user(
    db: Session,
    request: UserRegistrationRequest,
) -> UserRegistrationResponse:
    """Create a new user account from validated registration data."""

    normalized_email = request.email.strip().lower()

    existing_user = db.scalar(select(User).where(User.email == normalized_email))

    if existing_user is not None:
        raise DuplicateUserError("A user with this email already exists.")

    user = User(
        email=normalized_email,
        password_hash=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        status="registered",
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateUserError("A user with this email already exists.") from exc

    db.refresh(user)

    return UserRegistrationResponse.model_validate(user)
