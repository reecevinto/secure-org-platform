import secrets

SESSION_TOKEN_BYTES = 32


def generate_session_identifier() -> str:
    """Generate a cryptographically secure session identifier."""
    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)
