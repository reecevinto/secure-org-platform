from unittest.mock import patch

import pytest

from app.core.mfa_security import (
    decrypt_mfa_secret,
    encrypt_mfa_secret,
)


def test_encrypt_mfa_secret_returns_encrypted_value() -> None:
    secret = "JBSWY3DPEHPK3PXP"

    encrypted = encrypt_mfa_secret(secret)

    assert encrypted != secret
    assert encrypted


def test_encrypt_and_decrypt_mfa_secret_round_trip() -> None:
    secret = "JBSWY3DPEHPK3PXP"

    encrypted = encrypt_mfa_secret(secret)
    decrypted = decrypt_mfa_secret(encrypted)

    assert decrypted == secret


def test_encrypt_mfa_secret_produces_different_ciphertext() -> None:
    secret = "JBSWY3DPEHPK3PXP"

    first = encrypt_mfa_secret(secret)
    second = encrypt_mfa_secret(secret)

    assert first != second


def test_encrypt_mfa_secret_rejects_empty_secret() -> None:
    with pytest.raises(ValueError, match="MFA secret must not be empty"):
        encrypt_mfa_secret("")


def test_decrypt_mfa_secret_rejects_empty_value() -> None:
    with pytest.raises(
        ValueError,
        match="Encrypted MFA secret must not be empty",
    ):
        decrypt_mfa_secret("")


def test_decrypt_mfa_secret_rejects_invalid_ciphertext() -> None:
    with pytest.raises(ValueError, match="Unable to decrypt MFA secret"):
        decrypt_mfa_secret("not-valid-fernet-data")


def test_encrypt_mfa_secret_requires_encryption_key() -> None:
    with (
        patch("app.core.mfa_security.settings.mfa_encryption_key", ""),
        pytest.raises(
            RuntimeError,
            match="MFA encryption key is not configured",
        ),
    ):
        encrypt_mfa_secret("JBSWY3DPEHPK3PXP")


def test_encrypt_mfa_secret_rejects_invalid_encryption_key() -> None:
    with (
        patch(
            "app.core.mfa_security.settings.mfa_encryption_key",
            "invalid-key",
        ),
        pytest.raises(
            RuntimeError,
            match="MFA encryption key is invalid",
        ),
    ):
        encrypt_mfa_secret("JBSWY3DPEHPK3PXP")
