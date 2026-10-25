"""crear tabla instruments

Revision ID: 5c04b4e17055
Revises: b8d9aab32d68
Create Date: 2026-10-25 16:25:29.614570

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5c04b4e17055"
down_revision: str | Sequence[str] | None = "b8d9aab32d68"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "STOCK",
                "CEDEAR",
                "BOND",
                "ETF",
                "ON",
                "CRYPTO",
                name="instrument_type",
                native_enum=False,
                length=10,
            ),
            nullable=False,
        ),
        sa.Column(
            "market",
            sa.Enum(
                "BYMA", "NYSE", "NASDAQ", "CRYPTO", name="market", native_enum=False, length=10
            ),
            nullable=False,
        ),
        sa.Column(
            "currency", sa.Enum("ARS", "USD", name="currency", native_enum=False), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_instruments_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_instruments")),
        sa.UniqueConstraint(
            "user_id", "market", "ticker", name=op.f("uq_instruments_user_id_market_ticker")
        ),
    )
    op.create_index(op.f("ix_instruments_user_id"), "instruments", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_instruments_user_id"), table_name="instruments")
    op.drop_table("instruments")
