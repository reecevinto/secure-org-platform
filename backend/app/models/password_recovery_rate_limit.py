from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PasswordRecoveryRateLimit(Base):
    __tablename__ = "password_recovery_rate_limits"

    bucket_key_hash: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    window_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    request_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_password_recovery_rate_limits_expires_at",
            "expires_at",
        ),
    )
