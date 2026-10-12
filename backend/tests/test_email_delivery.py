from email.message import EmailMessage
from smtplib import SMTPException
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest

from app.core.config import settings
from app.services.email_delivery import (
    RecoveryEmailDeliveryError,
    send_recovery_email,
)


@pytest.fixture
def configured_smtp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.test")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_username", "smtp-user")
    monkeypatch.setattr(settings, "smtp_password", "smtp-password")
    monkeypatch.setattr(settings, "smtp_from_email", "noreply@example.test")
    monkeypatch.setattr(settings, "smtp_starttls", True)
    monkeypatch.setattr(settings, "smtp_use_ssl", False)
    monkeypatch.setattr(settings, "smtp_timeout_seconds", 10)
    monkeypatch.setattr(
        settings,
        "password_reset_url",
        "https://example.test/reset-password?source=recovery",
    )


def test_send_recovery_email_uses_starttls_and_encodes_token(
    configured_smtp: None,
) -> None:
    server = MagicMock()
    with patch("app.services.email_delivery.SMTP") as smtp_factory:
        smtp_factory.return_value.__enter__.return_value = server

        send_recovery_email(
            "user@example.test",
            "token+/=value",
        )

    smtp_factory.assert_called_once_with(
        "smtp.example.test",
        587,
        timeout=10,
    )
    server.ehlo.assert_any_call()
    server.starttls.assert_called_once_with()
    server.login.assert_called_once_with(
        "smtp-user",
        "smtp-password",
    )
    server.send_message.assert_called_once()

    message = server.send_message.call_args.args[0]
    assert isinstance(message, EmailMessage)
    assert message["To"] == "user@example.test"
    assert message["From"] == "noreply@example.test"

    body = message.get_content()
    reset_link = next(line for line in body.splitlines() if line.startswith("https://"))
    parsed_url = urlsplit(reset_link)

    assert parse_qs(parsed_url.query) == {
        "source": ["recovery"],
        "token": ["token+/=value"],
    }


def test_send_recovery_email_supports_implicit_ssl(
    configured_smtp: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "smtp_use_ssl", True)
    monkeypatch.setattr(settings, "smtp_starttls", False)
    monkeypatch.setattr(settings, "smtp_port", 465)

    server = MagicMock()
    with patch("app.services.email_delivery.SMTP_SSL") as smtp_ssl_factory:
        smtp_ssl_factory.return_value.__enter__.return_value = server

        send_recovery_email("user@example.test", "opaque-token")

    smtp_ssl_factory.assert_called_once_with(
        "smtp.example.test",
        465,
        timeout=10,
    )
    server.starttls.assert_not_called()
    server.send_message.assert_called_once()


def test_send_recovery_email_rejects_missing_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "smtp_host", "")
    monkeypatch.setattr(settings, "smtp_from_email", "")

    with pytest.raises(
        RecoveryEmailDeliveryError,
        match="not configured",
    ):
        send_recovery_email("user@example.test", "opaque-token")


def test_send_recovery_email_rejects_conflicting_tls_modes(
    configured_smtp: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "smtp_use_ssl", True)
    monkeypatch.setattr(settings, "smtp_starttls", True)

    with pytest.raises(
        RecoveryEmailDeliveryError,
        match="cannot both be enabled",
    ):
        send_recovery_email("user@example.test", "opaque-token")


def test_send_recovery_email_hides_smtp_failure_details(
    configured_smtp: None,
) -> None:
    with (
        patch(
            "app.services.email_delivery.SMTP",
            side_effect=SMTPException("private server diagnostic"),
        ),
        pytest.raises(RecoveryEmailDeliveryError) as exc_info,
    ):
        send_recovery_email(
            "user@example.test",
            "sensitive-token",
        )

    assert "private server diagnostic" not in str(exc_info.value)
    assert "sensitive-token" not in str(exc_info.value)
