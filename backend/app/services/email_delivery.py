from email.message import EmailMessage
from smtplib import SMTP, SMTP_SSL, SMTPException
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.core.config import settings


class RecoveryEmailDeliveryError(Exception):
    """Raised when a password recovery email cannot be delivered."""


def send_recovery_email(
    recipient: str,
    token: str,
) -> None:
    """Deliver a password recovery link using the configured SMTP server."""

    if not settings.smtp_host or not settings.smtp_from_email:
        raise RecoveryEmailDeliveryError(
            "Password recovery email delivery is not configured."
        )

    if settings.smtp_use_ssl and settings.smtp_starttls:
        raise RecoveryEmailDeliveryError(
            "SMTP SSL and STARTTLS cannot both be enabled."
        )

    parsed_url = urlsplit(settings.password_reset_url)
    query_params = [
        (key, value)
        for key, value in parse_qsl(
            parsed_url.query,
            keep_blank_values=True,
        )
        if key != "token"
    ]
    query_params.append(("token", token))

    reset_url = urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            urlencode(query_params),
            parsed_url.fragment,
        )
    )

    message = EmailMessage()
    message["Subject"] = "Password recovery"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message.set_content(
        "A request was made to reset your password.\n\n"
        "Use the following link to continue:\n"
        f"{reset_url}\n\n"
        "If you did not request this change, you can ignore this email.\n"
        "This link expires after a limited time and can only be used once."
    )

    try:
        if settings.smtp_use_ssl:
            with SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            ) as server:
                _authenticate_and_send(server, message, recipient)
        else:
            with SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            ) as server:
                if settings.smtp_starttls:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()

                _authenticate_and_send(server, message, recipient)

    except (OSError, SMTPException) as exc:
        raise RecoveryEmailDeliveryError(
            "Password recovery email delivery failed."
        ) from exc


def _authenticate_and_send(
    server: SMTP | SMTP_SSL,
    message: EmailMessage,
    recipient: str,
) -> None:
    if settings.smtp_username:
        server.login(
            settings.smtp_username,
            settings.smtp_password,
        )

    server.send_message(message, to_addrs=[recipient])
