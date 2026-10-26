"""crear tabla holding_snapshots

Revision ID: 92214b67a6db
Revises: 20d7c348dde8
Create Date: 2026-10-26 09:42:20.965626

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "92214b67a6db"
down_revision: str | Sequence[str] | None = "20d7c348dde8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "holding_snapshots",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("average_price", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("last_price", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name=op.f("fk_holding_snapshots_account_id_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.id"],
            name=op.f("fk_holding_snapshots_instrument_id_instruments"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_holding_snapshots_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_holding_snapshots")),
    )
    op.create_index(
        op.f("ix_holding_snapshots_account_id"), "holding_snapshots", ["account_id"], unique=False
    )
    op.create_index(
        op.f("ix_holding_snapshots_user_id"), "holding_snapshots", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_holding_snapshots_user_id"), table_name="holding_snapshots")
    op.drop_index(op.f("ix_holding_snapshots_account_id"), table_name="holding_snapshots")
    op.drop_table("holding_snapshots")
