import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.auth import get_password_recovery_rate_limiter
from app.core.database import get_db
from app.main import app
from app.schemas.auth import PasswordRecoveryResponse
from app.services.password_recovery import InvalidRecoveryTokenError
from app.services.password_recovery_rate_limit import RateLimitDecision

client = TestClient(app)


class AllowAllPasswordRecoveryRateLimiter:
    """Allow password-recovery requests in unrelated API tests."""

    def check(
        self,
        *,
        namespace: str,
        identifier: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        return RateLimitDecision(
            allowed=True,
            limit=limit,
            remaining=limit - 1,
            retry_after_seconds=60,
        )


@pytest.fixture(autouse=True)
def override_password_recovery_rate_limiter():
    """Keep unrelated API tests independent of PostgreSQL rate-limit storage."""

    limiter = AllowAllPasswordRecoveryRateLimiter()

    def override_limiter():
        return limiter

    app.dependency_overrides[get_password_recovery_rate_limiter] = override_limiter

    yield

    app.dependency_overrides.pop(
        get_password_recovery_rate_limiter,
        None,
    )


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


def test_forgot_password_returns_429_when_source_limit_is_exceeded() -> None:
    from app.api.auth import get_password_recovery_rate_limiter
    from app.services.password_recovery_rate_limit import RateLimitDecision

    db = create_mock_db()

    def override_get_db():
        yield db

    class DenySourceLimiter:
        def check(
            self,
            *,
            namespace: str,
            identifier: str,
            limit: int,
            window_seconds: int,
        ) -> RateLimitDecision:
            return RateLimitDecision(
                allowed=False,
                limit=limit,
                remaining=0,
                retry_after_seconds=120,
            )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_password_recovery_rate_limiter] = lambda: (
        DenySourceLimiter()
    )

    try:
        with patch(
            "app.api.auth.process_password_recovery_request",
        ) as recovery_mock:
            response = client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "user@example.com"},
            )

        assert response.status_code == 429
        assert response.headers["Retry-After"] == "120"
        recovery_mock.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_forgot_password_keeps_generic_response_when_email_limit_is_exceeded() -> None:
    from app.api.auth import get_password_recovery_rate_limiter
    from app.services.password_recovery_rate_limit import RateLimitDecision

    db = create_mock_db()

    def override_get_db():
        yield db

    class DenyEmailLimiter:
        def check(
            self,
            *,
            namespace: str,
            identifier: str,
            limit: int,
            window_seconds: int,
        ) -> RateLimitDecision:
            if namespace == "password-recovery-email":
                return RateLimitDecision(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    retry_after_seconds=300,
                )

            return RateLimitDecision(
                allowed=True,
                limit=limit,
                remaining=limit - 1,
                retry_after_seconds=60,
            )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_password_recovery_rate_limiter] = lambda: (
        DenyEmailLimiter()
    )

    expected = {
        "message": (
            "If an account matches that email address, "
            "password recovery instructions will be sent."
        )
    }

    try:
        with patch(
            "app.api.auth.process_password_recovery_request",
        ) as recovery_mock:
            response = client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "user@example.com"},
            )

        assert response.status_code == 200
        assert response.json() == expected
        recovery_mock.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_reset_password_returns_429_when_source_limit_is_exceeded() -> None:
    from app.api.auth import get_password_recovery_rate_limiter
    from app.services.password_recovery_rate_limit import RateLimitDecision

    db = create_mock_db()

    def override_get_db():
        yield db

    class DenyResetLimiter:
        def check(
            self,
            *,
            namespace: str,
            identifier: str,
            limit: int,
            window_seconds: int,
        ) -> RateLimitDecision:
            return RateLimitDecision(
                allowed=False,
                limit=limit,
                remaining=0,
                retry_after_seconds=90,
            )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_password_recovery_rate_limiter] = lambda: (
        DenyResetLimiter()
    )

    try:
        with patch(
            "app.api.auth.reset_password_service",
        ) as reset_mock:
            response = client.post(
                "/api/v1/auth/reset-password",
                json={
                    "token": "valid-recovery-token",
                    "new_password": "A-Strong-New-Password-123!",
                },
            )

        assert response.status_code == 429
        assert response.headers["Retry-After"] == "90"
        reset_mock.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_forgot_password_fails_closed_when_limiter_storage_fails() -> None:
    from app.api.auth import get_password_recovery_rate_limiter

    db = create_mock_db()

    def override_get_db():
        yield db

    class FailingLimiter:
        def check(
            self,
            *,
            namespace: str,
            identifier: str,
            limit: int,
            window_seconds: int,
        ):
            raise RuntimeError("database unavailable")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_password_recovery_rate_limiter] = lambda: (
        FailingLimiter()
    )

    try:
        with patch(
            "app.api.auth.process_password_recovery_request",
        ) as recovery_mock:
            response = client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "user@example.com"},
            )

        assert response.status_code == 503
        assert "database unavailable" not in response.text
        recovery_mock.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_forgot_password_does_not_trust_forwarded_for_header() -> None:
    captured_checks: list[dict[str, object]] = []

    class CapturingLimiter:
        def check(
            self,
            *,
            namespace: str,
            identifier: str,
            limit: int,
            window_seconds: int,
        ) -> RateLimitDecision:
            captured_checks.append(
                {
                    "namespace": namespace,
                    "identifier": identifier,
                }
            )
            return RateLimitDecision(
                allowed=True,
                limit=limit,
                remaining=limit - 1,
                retry_after_seconds=60,
            )

    app.dependency_overrides[get_password_recovery_rate_limiter] = lambda: (
        CapturingLimiter()
    )

    try:
        with patch("app.api.auth.process_password_recovery_request"):
            response = client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "user@example.com"},
                headers={"X-Forwarded-For": "203.0.113.99"},
            )

        assert response.status_code == 200
        assert captured_checks[0]["namespace"] == "password-recovery-source"
        assert captured_checks[0]["identifier"] == "testclient"
    finally:
        app.dependency_overrides.clear()
