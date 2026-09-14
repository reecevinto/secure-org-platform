from app.core.totp import generate_totp_secret


def test_generate_totp_secret_returns_value() -> None:
    secret = generate_totp_secret()

    assert secret


def test_generate_totp_secret_is_base32() -> None:
    secret = generate_totp_secret()

    assert secret == secret.upper()
    assert all(character in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for character in secret)


def test_generate_totp_secret_has_expected_length() -> None:
    secret = generate_totp_secret()

    assert len(secret) == 32


def test_generate_totp_secret_is_unique() -> None:
    first = generate_totp_secret()
    second = generate_totp_secret()

    assert first != second
