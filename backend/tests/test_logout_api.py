from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_logout_revokes_existing_session(monkeypatch) -> None:
    revoked_session = object()

    def mock_revoke_session(
        db,
        session_identifier: str,
    ):
        assert session_identifier == "valid-session-identifier"
        return revoked_session

    monkeypatch.setattr(
        "app.api.auth.revoke_session",
        mock_revoke_session,
    )

    response = client.post(
        "/api/v1/auth/logout",
        json={"session_identifier": "valid-session-identifier"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Logout successful."}


def test_logout_returns_not_found_for_unknown_session(monkeypatch) -> None:
    def mock_revoke_session(
        db,
        session_identifier: str,
    ):
        return None

    monkeypatch.setattr(
        "app.api.auth.revoke_session",
        mock_revoke_session,
    )

    response = client.post(
        "/api/v1/auth/logout",
        json={"session_identifier": "unknown-session-identifier"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found."}


def test_logout_requires_session_identifier() -> None:
    response = client.post(
        "/api/v1/auth/logout",
        json={},
    )

    assert response.status_code == 422


def test_logout_rejects_empty_session_identifier() -> None:
    response = client.post(
        "/api/v1/auth/logout",
        json={"session_identifier": ""},
    )

    assert response.status_code == 422


def test_logout_does_not_return_session_data(monkeypatch) -> None:
    def mock_revoke_session(
        db,
        session_identifier: str,
    ):
        return object()

    monkeypatch.setattr(
        "app.api.auth.revoke_session",
        mock_revoke_session,
    )

    response = client.post(
        "/api/v1/auth/logout",
        json={"session_identifier": "valid-session-identifier"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Logout successful."}
    assert "session_identifier" not in response.json()
    assert "user_id" not in response.json()
    assert "revoked_at" not in response.json()
