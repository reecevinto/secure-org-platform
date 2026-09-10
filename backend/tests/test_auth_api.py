import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app

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
