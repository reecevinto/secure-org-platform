import json
from datetime import UTC, datetime
from uuid import UUID

from cryptography.fernet import InvalidToken

from app.core.config import settings
from app.core.mfa_security import get_mfa_fernet

MFA_LOGIN_CHALLENGE_PURPOSE = "mfa-login"


class MFAChallengeError(Exception):
    """Raised when an MFA login challenge is invalid."""


def create_mfa_challenge(
    user_id: UUID,
    issued_at: datetime | None = None,
) -> str:
    """Create a short-lived encrypted MFA login challenge."""

    if issued_at is None:
        issued_at = datetime.now(UTC)

    if issued_at.tzinfo is None:
        raise ValueError("MFA challenge timestamp must be timezone-aware.")

    payload = json.dumps(
        {
            "purpose": MFA_LOGIN_CHALLENGE_PURPOSE,
            "user_id": str(user_id),
        },
        separators=(",", ":"),
    ).encode()

    token = get_mfa_fernet().encrypt_at_time(
        payload,
        current_time=int(issued_at.timestamp()),
    )

    return token.decode()


def verify_mfa_challenge(challenge: str) -> UUID:
    """Validate an MFA login challenge and return its trusted user ID."""

    if not challenge:
        raise MFAChallengeError("MFA verification failed.")

    try:
        decrypted = get_mfa_fernet().decrypt(
            challenge.encode(),
            ttl=settings.mfa_challenge_ttl_seconds,
        )

        payload = json.loads(decrypted.decode())

        if payload.get("purpose") != MFA_LOGIN_CHALLENGE_PURPOSE:
            raise MFAChallengeError("MFA verification failed.")

        return UUID(payload["user_id"])

    except (
        InvalidToken,
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise MFAChallengeError("MFA verification failed.") from exc
