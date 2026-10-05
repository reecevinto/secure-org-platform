from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.mfa_challenge import (
    MFAChallengeError,
    create_mfa_challenge,
    verify_mfa_challenge,
)


def test_create_and_verify_mfa_challenge() -> None:
    user_id = uuid4()

    challenge = create_mfa_challenge(user_id)

    assert challenge
    assert verify_mfa_challenge(challenge) == user_id


def test_mfa_challenge_does_not_expose_user_id() -> None:
    user_id = uuid4()

    challenge = create_mfa_challenge(user_id)

    assert str(user_id) not in challenge


def test_mfa_challenge_rejects_tampering() -> None:
    user_id = uuid4()

    challenge = create_mfa_challenge(user_id)

    replacement = "A" if challenge[-1] != "A" else "B"
    tampered_challenge = challenge[:-1] + replacement

    with pytest.raises(MFAChallengeError):
        verify_mfa_challenge(tampered_challenge)


def test_mfa_challenge_rejects_expired_challenge() -> None:
    user_id = uuid4()

    challenge = create_mfa_challenge(
        user_id=user_id,
        issued_at=datetime.now(UTC) - timedelta(minutes=10),
    )

    with pytest.raises(MFAChallengeError):
        verify_mfa_challenge(challenge)


def test_mfa_challenge_rejects_wrong_purpose() -> None:
    import json

    from app.core.mfa_security import get_mfa_fernet

    user_id = uuid4()

    payload = json.dumps(
        {
            "purpose": "wrong-purpose",
            "user_id": str(user_id),
        }
    ).encode()

    challenge = get_mfa_fernet().encrypt(payload).decode()

    with pytest.raises(MFAChallengeError):
        verify_mfa_challenge(challenge)
