"""create password recovery rate limits table

Revision ID: 4a6d9c2e7f31
Revises: 2df7b680d5c2
Create Date: 2026-10-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "4a6d9c2e7f31"
down_revision: str | Sequence[str] | None = "2df7b680d5c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create shared password-recovery rate-limit storage."""
    op.create_table(
        "password_recovery_rate_limits",
        sa.Column("bucket_key_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "window_started_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("bucket_key_hash"),
    )

    op.create_index(
        "ix_password_recovery_rate_limits_expires_at",
        "password_recovery_rate_limits",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove shared password-recovery rate-limit storage."""
    op.drop_index(
        "ix_password_recovery_rate_limits_expires_at",
        table_name="password_recovery_rate_limits",
    )
    op.drop_table("password_recovery_rate_limits")
