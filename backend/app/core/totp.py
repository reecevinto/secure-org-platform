import pyotp


def generate_totp_secret() -> str:
    """Generate a cryptographically secure TOTP secret."""

    return pyotp.random_base32()
