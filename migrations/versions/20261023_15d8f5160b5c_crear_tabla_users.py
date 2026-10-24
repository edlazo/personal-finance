"""crear tabla users

Revision ID: 15d8f5160b5c
Revises:
Create Date: 2026-10-23 21:52:26.096541

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "15d8f5160b5c"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "default_rate_type",
            sa.Enum(
                "MEP",
                "OFICIAL",
                "BLUE",
                "CCL",
                "CRIPTO",
                name="rate_type",
                native_enum=False,
                length=10,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "default_rate_type IN ('MEP', 'OFICIAL', 'BLUE', 'CCL', 'CRIPTO')",
            name=op.f("ck_users_rate_type"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )


def downgrade() -> None:
    op.drop_table("users")
