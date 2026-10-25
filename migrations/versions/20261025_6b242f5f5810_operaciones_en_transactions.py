"""operaciones en transactions

Revision ID: 6b242f5f5810
Revises: 5c04b4e17055
Create Date: 2026-10-25 18:32:43.886413

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6b242f5f5810"
down_revision: str | Sequence[str] | None = "5c04b4e17055"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("trade_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_transactions_trade_id"), "transactions", ["trade_id"], unique=False)
    op.drop_constraint(op.f("ck_transactions_category_or_transfer"), "transactions", type_="check")
    op.create_check_constraint(
        op.f("ck_transactions_category_transfer_or_trade"),
        "transactions",
        "num_nonnulls(category_id, transfer_group_id, trade_id) = 1",
    )


def downgrade() -> None:
    # Falla si ya hay movimientos de operaciones: borrarlos es decisión de quien hace el downgrade.
    op.drop_constraint(
        op.f("ck_transactions_category_transfer_or_trade"), "transactions", type_="check"
    )
    op.create_check_constraint(
        op.f("ck_transactions_category_or_transfer"),
        "transactions",
        "(category_id IS NULL) <> (transfer_group_id IS NULL)",
    )
    op.drop_index(op.f("ix_transactions_trade_id"), table_name="transactions")
    op.drop_column("transactions", "trade_id")
