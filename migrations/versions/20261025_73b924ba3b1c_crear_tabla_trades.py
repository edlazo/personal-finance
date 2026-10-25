"""crear tabla trades

Revision ID: 73b924ba3b1c
Revises: 6b242f5f5810
Create Date: 2026-10-25 18:36:54.116383

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "73b924ba3b1c"
down_revision: str | Sequence[str] | None = "6b242f5f5810"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trades",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column(
            "side", sa.Enum("BUY", "SELL", name="trade_side", native_enum=False), nullable=False
        ),
        sa.Column("quantity", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("price", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("fee", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name=op.f("fk_trades_account_id_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instruments.id"], name=op.f("fk_trades_instrument_id_instruments")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_trades_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trades")),
    )
    op.create_index(op.f("ix_trades_account_id"), "trades", ["account_id"], unique=False)
    op.create_index(op.f("ix_trades_instrument_id"), "trades", ["instrument_id"], unique=False)
    op.create_index(op.f("ix_trades_user_id"), "trades", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trades_user_id"), table_name="trades")
    op.drop_index(op.f("ix_trades_instrument_id"), table_name="trades")
    op.drop_index(op.f("ix_trades_account_id"), table_name="trades")
    op.drop_table("trades")
