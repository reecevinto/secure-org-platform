import uuid

from sqlalchemy import select

from app.models.user import User


def test_register_user_persists_to_postgresql(
    integration_client,
    unique_test_email: str,
) -> None:
    client, db = integration_client

    try:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_test_email,
                "password": "CorrectHorseBatteryStaple!",
                "first_name": "Integration",
                "last_name": "Test",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["email"] == unique_test_email
        assert data["first_name"] == "Integration"
        assert data["last_name"] == "Test"
        assert data["status"] == "registered"
        assert "password" not in data
        assert "password_hash" not in data

        user = db.scalar(select(User).where(User.email == unique_test_email))

        assert user is not None
        assert user.email == unique_test_email
        assert user.first_name == "Integration"
        assert user.last_name == "Test"
        assert user.status == "registered"
        assert user.password_hash.startswith("$argon2id$")
        assert user.password_hash != "CorrectHorseBatteryStaple!"
        assert str(user.id) == data["id"]
        assert uuid.UUID(data["id"]) == user.id

    finally:
        user = db.scalar(select(User).where(User.email == unique_test_email))

        if user is not None:
            db.delete(user)
            db.commit()


def test_register_user_rejects_duplicate_email_in_postgresql(
    integration_client,
    unique_test_email: str,
) -> None:
    client, db = integration_client

    try:
        registration_data = {
            "email": unique_test_email,
            "password": "CorrectHorseBatteryStaple!",
            "first_name": "Integration",
            "last_name": "Test",
        }

        first_response = client.post(
            "/api/v1/auth/register",
            json=registration_data,
        )

        assert first_response.status_code == 201

        duplicate_response = client.post(
            "/api/v1/auth/register",
            json=registration_data,
        )

        assert duplicate_response.status_code == 409
        assert duplicate_response.json() == {
            "detail": "A user with this email already exists."
        }

        users = db.scalars(select(User).where(User.email == unique_test_email)).all()

        assert len(users) == 1

    finally:
        user = db.scalar(select(User).where(User.email == unique_test_email))

        if user is not None:
            db.delete(user)
            db.commit()
