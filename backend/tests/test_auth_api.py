import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.schemas.auth import PasswordRecoveryResponse
from app.services.password_recovery import InvalidRecoveryTokenError

client = TestClient(app)


def create_mock_db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    def refresh_user(user: object) -> None:
        user.id = uuid.uuid4()  # type: ignore[attr-defined]

    db.refresh.side_effect = refresh_user

    return db


def test_register_user_returns_created_user() -> None:
    db = create_mock_db()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "User@Example.COM",
                "password": "CorrectHorseBatteryStaple!",
                "first_name": "Example",
                "last_name": "User",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["email"] == "user@example.com"
        assert data["first_name"] == "Example"
        assert data["last_name"] == "User"
        assert data["status"] == "registered"
        assert "password" not in data
        assert "password_hash" not in data
    finally:
        app.dependency_overrides.clear()


def test_register_user_rejects_invalid_email() -> None:
    db = create_mock_db()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "CorrectHorseBatteryStaple!",
                "first_name": "Example",
                "last_name": "User",
            },
        )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_register_user_requires_registration_fields() -> None:
    db = create_mock_db()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "CorrectHorseBatteryStaple!",
                "first_name": "Example",
            },
        )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_register_user_rejects_duplicate_email() -> None:
    db = create_mock_db()
    db.scalar.return_value = MagicMock()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "CorrectHorseBatteryStaple!",
                "first_name": "Example",
                "last_name": "User",
            },
        )

        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_login_user_returns_authenticated_user() -> None:
    db = create_mock_db()

    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "user@example.com"
    user.password_hash = "$argon2id$example-hash"
    user.first_name = "Example"
    user.last_name = "User"
    user.status = "registered"

    db.scalar.return_value = user

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.services.login.verify_password",
            return_value=True,
        ):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "User@Example.COM",
                    "password": "CorrectHorseBatteryStaple!",
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == str(user.id)
        assert data["email"] == "user@example.com"
        assert data["first_name"] == "Example"
        assert data["last_name"] == "User"
        assert data["status"] == "registered"
        assert "password" not in data
        assert "password_hash" not in data
    finally:
        app.dependency_overrides.clear()


def test_login_user_rejects_incorrect_password() -> None:
    db = create_mock_db()

    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "user@example.com"
    user.password_hash = "$argon2id$example-hash"
    user.first_name = "Example"
    user.last_name = "User"
    user.status = "registered"

    db.scalar.return_value = user

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.services.login.verify_password",
            return_value=False,
        ):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "user@example.com",
                    "password": "WrongPassword!",
                },
            )

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Invalid email or password.",
        }
    finally:
        app.dependency_overrides.clear()


def test_login_user_rejects_unknown_email() -> None:
    db = create_mock_db()
    db.scalar.return_value = None

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "unknown@example.com",
                "password": "CorrectHorseBatteryStaple!",
            },
        )

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Invalid email or password.",
        }
    finally:
        app.dependency_overrides.clear()


def test_login_user_rejects_invalid_email() -> None:
    db = create_mock_db()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "not-an-email",
                "password": "CorrectHorseBatteryStaple!",
            },
        )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_login_user_requires_password() -> None:
    db = create_mock_db()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
            },
        )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_forgot_password_returns_generic_response() -> None:
    db = create_mock_db()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    expected = {
        "message": (
            "If an account matches that email address, "
            "password recovery instructions will be sent."
        )
    }

    try:
        with patch(
            "app.api.auth.process_password_recovery_request",
            return_value=PasswordRecoveryResponse(),
        ) as recovery_mock:
            response = client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "User@Example.COM"},
            )

        assert response.status_code == 200
        assert response.json() == expected
        recovery_mock.assert_called_once()
        recovery_mock.assert_called_once_with("user@example.com")
    finally:
        app.dependency_overrides.clear()


def test_forgot_password_rejects_invalid_email() -> None:
    db = create_mock_db()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.api.auth.process_password_recovery_request",
        ) as recovery_mock:
            response = client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "not-an-email"},
            )

        assert response.status_code == 422
        recovery_mock.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_forgot_password_requires_email() -> None:
    db = create_mock_db()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.api.auth.process_password_recovery_request",
        ) as recovery_mock:
            response = client.post(
                "/api/v1/auth/forgot-password",
                json={},
            )

        assert response.status_code == 422
        recovery_mock.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_reset_password_returns_success_for_valid_token() -> None:
    db = create_mock_db()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.api.auth.reset_password_service",
        ) as reset_mock:
            reset_mock.return_value.message = "Password reset successful."

            response = client.post(
                "/api/v1/auth/reset-password",
                json={
                    "token": "valid-recovery-token",
                    "new_password": "A-Strong-New-Password-123!",
                },
            )

        assert response.status_code == 200
        assert response.json() == {
            "message": "Password reset successful.",
        }
        reset_mock.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_reset_password_rejects_invalid_token() -> None:
    db = create_mock_db()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.api.auth.reset_password_service",
            side_effect=InvalidRecoveryTokenError("Internal token detail"),
        ):
            response = client.post(
                "/api/v1/auth/reset-password",
                json={
                    "token": "invalid-token",
                    "new_password": "A-Strong-New-Password-123!",
                },
            )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "Invalid or expired password reset token.",
        }
        assert "Internal token detail" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_reset_password_rejects_missing_fields() -> None:
    db = create_mock_db()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.api.auth.reset_password_service",
        ) as reset_mock:
            response = client.post(
                "/api/v1/auth/reset-password",
                json={"token": "some-token"},
            )

        assert response.status_code == 422
        reset_mock.assert_not_called()
    finally:
        app.dependency_overrides.clear()
