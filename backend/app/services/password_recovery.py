import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.password_recovery_token import PasswordRecoveryToken
from app.models.session import Session as AuthSession
from app.models.user import User
from app.schemas.auth import (
    PasswordRecoveryRequest,
    PasswordRecoveryResponse,
    PasswordResetRequest,
    PasswordResetResponse,
)
from app.services.email_delivery import (
    RecoveryEmailDeliveryError,
    send_recovery_email,
)


def process_password_recovery_request(email: str) -> None:
    """Process a recovery request in a background task with its own DB session."""
    from app.schemas.auth import PasswordRecoveryRequest

    db = SessionLocal()
    try:
        request = PasswordRecoveryRequest(email=email)
        request_password_recovery(db=db, request=request)
    except Exception:
        import logging

        logging.getLogger(__name__).exception(
            "Password recovery request processing failed."
        )
    finally:
        db.close()


class InvalidRecoveryTokenError(Exception):
    """Raised when a password recovery token is invalid or unusable."""


def _hash_recovery_token(token: str) -> str:
    """Return the SHA-256 digest of a recovery token."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def request_password_recovery(
    db: Session,
    request: PasswordRecoveryRequest,
) -> PasswordRecoveryResponse:
    """Issue a recovery token without disclosing whether an account exists."""

    response = PasswordRecoveryResponse()
    normalized_email = request.email.strip().lower()

    user = db.scalar(
        select(User).where(
            User.email == normalized_email,
            User.deleted_at.is_(None),
        )
    )

    if user is None:
        return response

    raw_token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)

    recovery_token = PasswordRecoveryToken(
        user_id=user.id,
        token_hash=_hash_recovery_token(raw_token),
        expires_at=now
        + timedelta(seconds=settings.password_recovery_token_ttl_seconds),
    )

    try:
        db.add(recovery_token)
        db.commit()
    except Exception:
        db.rollback()
        raise

    try:
        send_recovery_email(recipient=user.email, token=raw_token)
    except RecoveryEmailDeliveryError:
        try:
            recovery_token.used_at = datetime.now(UTC)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise
        return response

    return response


def reset_password(
    db: Session,
    request: PasswordResetRequest,
) -> PasswordResetResponse:
    """Reset a password and revoke active sessions atomically."""

    token_hash = _hash_recovery_token(request.token)
    now = datetime.now(UTC)

    try:
        # Initially read the token to identify its account.
        candidate_token = db.scalar(
            select(PasswordRecoveryToken).where(
                PasswordRecoveryToken.token_hash == token_hash,
            )
        )

        if candidate_token is None:
            raise InvalidRecoveryTokenError(
                "The password reset token is invalid or expired."
            )

        # Lock the user before the token to establish a consistent lock order.
        user = db.scalar(
            select(User)
            .where(
                User.id == candidate_token.user_id,
                User.deleted_at.is_(None),
            )
            .with_for_update()
        )

        if user is None:
            raise InvalidRecoveryTokenError(
                "The password reset token is invalid or expired."
            )

        # Lock and refresh the token after acquiring the user lock.
        recovery_token = db.scalar(
            select(PasswordRecoveryToken)
            .where(
                PasswordRecoveryToken.id == candidate_token.id,
                PasswordRecoveryToken.user_id == user.id,
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )

        # Validate again because another transaction may have used the token.
        if (
            recovery_token is None
            or recovery_token.used_at is not None
            or recovery_token.expires_at <= now
        ):
            raise InvalidRecoveryTokenError(
                "The password reset token is invalid or expired."
            )

        user.password_hash = hash_password(request.new_password)
        recovery_token.used_at = now

        # Invalidate every outstanding recovery token for this account.
        db.execute(
            update(PasswordRecoveryToken)
            .where(
                PasswordRecoveryToken.user_id == user.id,
                PasswordRecoveryToken.used_at.is_(None),
            )
            .values(used_at=now)
        )

        # Revoke active sessions as part of the same transaction.
        db.execute(
            update(AuthSession)
            .where(
                AuthSession.user_id == user.id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

        db.commit()

    except InvalidRecoveryTokenError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    return PasswordResetResponse()
