from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _get_fernet() -> Fernet:
    """Create a Fernet cipher using the configured MFA encryption key."""

    if not settings.mfa_encryption_key:
        raise RuntimeError("MFA encryption key is not configured.")

    try:
        return Fernet(settings.mfa_encryption_key.encode())
    except (ValueError, TypeError) as exc:
        raise RuntimeError("MFA encryption key is invalid.") from exc


def encrypt_mfa_secret(secret: str) -> str:
    """Encrypt an MFA secret for secure persistence."""

    if not secret:
        raise ValueError("MFA secret must not be empty.")

    encrypted = _get_fernet().encrypt(secret.encode())

    return encrypted.decode()


def decrypt_mfa_secret(encrypted_secret: str) -> str:
    """Decrypt a persisted MFA secret."""

    if not encrypted_secret:
        raise ValueError("Encrypted MFA secret must not be empty.")

    try:
        decrypted = _get_fernet().decrypt(encrypted_secret.encode())
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt MFA secret.") from exc

    return decrypted.decode()
