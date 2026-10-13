from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

import app.services.password_recovery_rate_limit as rate_limit_module
from app.services.password_recovery_rate_limit import (
    PasswordRecoveryRateLimiter,
)


@pytest.fixture
def fixed_now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


@pytest.fixture
def mock_db() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture
def limiter(
    mock_db: MagicMock,
    fixed_now: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> PasswordRecoveryRateLimiter:
    monkeypatch.setattr(rate_limit_module, "_last_cleanup_at", 0.0)
    monkeypatch.setattr(rate_limit_module, "monotonic", lambda: 1000.0)

    return PasswordRecoveryRateLimiter(
        db=mock_db,
        hmac_key="test-only-dedicated-secret-key-123456",
        clock=lambda: fixed_now,
    )


def configure_database_result(
    mock_db: MagicMock,
    *,
    request_count: int,
    expires_at: datetime,
) -> None:
    cleanup_result = MagicMock()
    upsert_result = MagicMock()
    upsert_result.one.return_value = SimpleNamespace(
        request_count=request_count,
        expires_at=expires_at,
    )
    mock_db.execute.side_effect = [cleanup_result, upsert_result]


def test_rate_limiter_allows_requests_within_limit(
    limiter: PasswordRecoveryRateLimiter,
    mock_db: MagicMock,
    fixed_now: datetime,
) -> None:
    configure_database_result(
        mock_db,
        request_count=2,
        expires_at=fixed_now + timedelta(seconds=60),
    )

    decision = limiter.check(
        namespace="password-recovery-source",
        identifier="192.0.2.10",
        limit=3,
        window_seconds=60,
    )

    assert decision.allowed is True
    assert decision.limit == 3
    assert decision.remaining == 1
    assert decision.retry_after_seconds == 60
    mock_db.commit.assert_called_once()


def test_rate_limiter_denies_requests_over_limit(
    limiter: PasswordRecoveryRateLimiter,
    mock_db: MagicMock,
    fixed_now: datetime,
) -> None:
    configure_database_result(
        mock_db,
        request_count=4,
        expires_at=fixed_now + timedelta(seconds=45),
    )

    decision = limiter.check(
        namespace="password-recovery-source",
        identifier="192.0.2.10",
        limit=3,
        window_seconds=60,
    )

    assert decision.allowed is False
    assert decision.remaining == 0
    assert decision.retry_after_seconds == 45


def test_rate_limiter_uses_hashed_bucket_identifiers(
    limiter: PasswordRecoveryRateLimiter,
) -> None:
    source_bucket = limiter._hash_bucket(
        "password-recovery-source",
        "192.0.2.10",
    )
    email_bucket = limiter._hash_bucket(
        "password-recovery-email",
        "user@example.com",
    )

    assert len(source_bucket) == 64
    assert len(email_bucket) == 64
    assert source_bucket != email_bucket
    assert "192.0.2.10" not in source_bucket
    assert "user@example.com" not in email_bucket


def test_rate_limiter_rejects_short_hmac_key(
    mock_db: MagicMock,
) -> None:
    with pytest.raises(ValueError, match="at least 32 bytes"):
        PasswordRecoveryRateLimiter(
            db=mock_db,
            hmac_key="too-short",
        )


@pytest.mark.parametrize(
    ("namespace", "identifier", "limit", "window_seconds"),
    [
        ("", "identifier", 3, 60),
        ("namespace", "", 3, 60),
        ("namespace", "identifier", 0, 60),
        ("namespace", "identifier", 3, 0),
    ],
)
def test_rate_limiter_rejects_invalid_arguments(
    limiter: PasswordRecoveryRateLimiter,
    namespace: str,
    identifier: str,
    limit: int,
    window_seconds: int,
) -> None:
    with pytest.raises(ValueError):
        limiter.check(
            namespace=namespace,
            identifier=identifier,
            limit=limit,
            window_seconds=window_seconds,
        )


def test_rate_limiter_rolls_back_when_storage_fails(
    limiter: PasswordRecoveryRateLimiter,
    mock_db: MagicMock,
) -> None:
    mock_db.execute.side_effect = RuntimeError("database unavailable")

    with pytest.raises(RuntimeError, match="database unavailable"):
        limiter.check(
            namespace="password-recovery-source",
            identifier="192.0.2.10",
            limit=3,
            window_seconds=60,
        )

    mock_db.rollback.assert_called_once()
    mock_db.commit.assert_not_called()


def test_rate_limiter_uses_atomic_postgresql_upsert(
    limiter: PasswordRecoveryRateLimiter,
    mock_db: MagicMock,
    fixed_now: datetime,
) -> None:
    configure_database_result(
        mock_db,
        request_count=1,
        expires_at=fixed_now + timedelta(seconds=60),
    )

    limiter.check(
        namespace="password-recovery-source",
        identifier="192.0.2.10",
        limit=3,
        window_seconds=60,
    )

    statement = mock_db.execute.call_args_list[1].args[0]
    compiled = statement.compile(dialect=postgresql.dialect())

    assert "ON CONFLICT" in str(compiled).upper()
    assert "DO UPDATE" in str(compiled).upper()
    assert "request_count" in compiled.params
    assert all("192.0.2.10" != value for value in compiled.params.values())


def test_rate_limiter_does_not_mark_cleanup_complete_after_rollback(
    limiter: PasswordRecoveryRateLimiter,
    mock_db: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rate_limit_module, "_last_cleanup_at", 0.0)
    monkeypatch.setattr(rate_limit_module, "monotonic", lambda: 1000.0)
    mock_db.execute.side_effect = RuntimeError("database unavailable")

    with pytest.raises(RuntimeError, match="database unavailable"):
        limiter.check(
            namespace="password-recovery-source",
            identifier="192.0.2.10",
            limit=3,
            window_seconds=60,
        )

    assert rate_limit_module._last_cleanup_at == 0.0
    mock_db.rollback.assert_called_once()
    mock_db.commit.assert_not_called()
