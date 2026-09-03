from app.core.security import hash_password, verify_password


def test_hash_password_does_not_return_plaintext() -> None:
    password = "CorrectHorseBatteryStaple!"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")


def test_hash_password_produces_unique_hashes() -> None:
    password = "CorrectHorseBatteryStaple!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash


def test_verify_password_accepts_correct_password() -> None:
    password = "CorrectHorseBatteryStaple!"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_verify_password_rejects_incorrect_password() -> None:
    password_hash = hash_password("CorrectHorseBatteryStaple!")

    assert verify_password("WrongPassword!", password_hash) is False


def test_verify_password_rejects_malformed_hash() -> None:
    assert verify_password("CorrectHorseBatteryStaple!", "not-a-valid-hash") is False


def test_verify_password_rejects_tampered_hash() -> None:
    password = "CorrectHorseBatteryStaple!"
    password_hash = hash_password(password)

    tampered_hash = f"{password_hash}tampered"

    assert verify_password(password, tampered_hash) is False
