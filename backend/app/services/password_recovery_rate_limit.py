import hmac
import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from threading import Lock
from time import monotonic
from typing import cast

from sqlalchemy import Table, case, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.password_recovery_rate_limit import (
    PasswordRecoveryRateLimit,
)

_last_cleanup_at = 0.0
_cleanup_lock = Lock()


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


class PasswordRecoveryRateLimiter:
    """Enforce atomic, shared PostgreSQL fixed-window rate limits."""

    def __init__(
        self,
        db: Session,
        hmac_key: str,
        clock: Callable[[], datetime] | None = None,
        cleanup_interval_seconds: int = 60,
    ) -> None:
        if len(hmac_key.encode("utf-8")) < 32:
            raise ValueError(
                "The password-recovery rate-limit HMAC key "
                "must contain at least 32 bytes."
            )

        if cleanup_interval_seconds <= 0:
            raise ValueError("Cleanup interval must be positive.")

        self.db = db
        self._hmac_key = hmac_key.encode("utf-8")
        self._clock = clock or (lambda: datetime.now(UTC))
        self._cleanup_interval_seconds = cleanup_interval_seconds

    def _hash_bucket(self, namespace: str, identifier: str) -> str:
        message = f"{namespace}:{identifier}".encode()
        return hmac.new(
            self._hmac_key,
            message,
            sha256,
        ).hexdigest()

    def _cleanup_expired(self, now: datetime) -> bool:
        current_monotonic = monotonic()

        with _cleanup_lock:
            if current_monotonic - _last_cleanup_at < self._cleanup_interval_seconds:
                return False

            self.db.execute(
                delete(PasswordRecoveryRateLimit).where(
                    PasswordRecoveryRateLimit.expires_at <= now,
                ),
            )

        return True

    def check(
        self,
        namespace: str,
        identifier: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        if not namespace or not identifier:
            raise ValueError("Rate-limit namespace and identifier are required.")

        if limit <= 0 or window_seconds <= 0:
            raise ValueError("Rate limit and window must be positive.")

        now = self._clock()
        expires_at = now + timedelta(seconds=window_seconds)
        bucket_key_hash = self._hash_bucket(namespace, identifier)
        table = cast(Table, PasswordRecoveryRateLimit.__table__)

        statement = insert(table).values(
            bucket_key_hash=bucket_key_hash,
            window_started_at=now,
            request_count=1,
            expires_at=expires_at,
        )

        upsert_statement = statement.on_conflict_do_update(
            index_elements=[table.c.bucket_key_hash],
            set_={
                "window_started_at": case(
                    (table.c.expires_at <= now, now),
                    else_=table.c.window_started_at,
                ),
                "request_count": case(
                    (table.c.expires_at <= now, 1),
                    (
                        table.c.request_count <= limit,
                        table.c.request_count + 1,
                    ),
                    else_=limit + 1,
                ),
                "expires_at": case(
                    (table.c.expires_at <= now, expires_at),
                    else_=table.c.expires_at,
                ),
            },
        ).returning(
            table.c.request_count,
            table.c.expires_at,
        )

        cleanup_performed = False

        try:
            cleanup_performed = self._cleanup_expired(now)
            row = self.db.execute(upsert_statement).one()
            self.db.commit()

            if cleanup_performed:
                global _last_cleanup_at
                with _cleanup_lock:
                    _last_cleanup_at = monotonic()

        except Exception:
            self.db.rollback()
            raise

        request_count = row.request_count
        bucket_expires_at = row.expires_at

        retry_after = max(
            1,
            math.ceil((bucket_expires_at - now).total_seconds()),
        )

        return RateLimitDecision(
            allowed=request_count <= limit,
            limit=limit,
            remaining=max(0, limit - request_count),
            retry_after_seconds=retry_after,
        )
