import uuid

from sqlalchemy import select

from app.core.security import verify_password
from app.models.user import User


def test_login_user_authenticates_against_postgresql(
    integration_client,
    unique_test_email: str,
) -> None:
    client, db = integration_client
    password = "CorrectHorseBatteryStaple!"

    try:
        registration_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_test_email,
                "password": password,
                "first_name": "Integration",
                "last_name": "Login",
            },
        )

        assert registration_response.status_code == 201

        user = db.scalar(select(User).where(User.email == unique_test_email))

        assert user is not None
        assert user.password_hash.startswith("$argon2id$")
        assert verify_password(password, user.password_hash) is True

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_test_email,
                "password": password,
            },
        )

        assert login_response.status_code == 200

        data = login_response.json()

        assert data["id"] == str(user.id)
        assert data["email"] == unique_test_email
        assert data["first_name"] == "Integration"
        assert data["last_name"] == "Login"
        assert data["status"] == "registered"
        assert "password" not in data
        assert "password_hash" not in data

    finally:
        user = db.scalar(select(User).where(User.email == unique_test_email))

        if user is not None:
            db.delete(user)
            db.commit()


def test_login_user_rejects_wrong_password_in_postgresql(
    integration_client,
    unique_test_email: str,
) -> None:
    client, db = integration_client

    try:
        registration_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_test_email,
                "password": "CorrectHorseBatteryStaple!",
                "first_name": "Integration",
                "last_name": "Login",
            },
        )

        assert registration_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_test_email,
                "password": "WrongPassword!",
            },
        )

        assert login_response.status_code == 401
        assert login_response.json() == {"detail": "Invalid email or password."}

    finally:
        user = db.scalar(select(User).where(User.email == unique_test_email))

        if user is not None:
            db.delete(user)
            db.commit()


def test_login_user_rejects_unknown_email_in_postgresql(
    integration_client,
    unique_test_email: str,
) -> None:
    client, db = integration_client

    unknown_email = f"unknown-{uuid.uuid4()}@example.com"

    try:
        registration_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_test_email,
                "password": "CorrectHorseBatteryStaple!",
                "first_name": "Integration",
                "last_name": "Login",
            },
        )

        assert registration_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": unknown_email,
                "password": "CorrectHorseBatteryStaple!",
            },
        )

        assert login_response.status_code == 401
        assert login_response.json() == {"detail": "Invalid email or password."}

    finally:
        user = db.scalar(select(User).where(User.email == unique_test_email))

        if user is not None:
            db.delete(user)
            db.commit()
