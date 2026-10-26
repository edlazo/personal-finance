"""rentas ligadas a inversiones

Revision ID: 545d408c04e8
Revises: b184ae28a6f3
Create Date: 2026-10-26 08:13:14.022666

"""

from collections.abc import Sequence

from alembic import op

revision: str = "545d408c04e8"
down_revision: str | Sequence[str] | None = "b184ae28a6f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Un dividendo o cupón es un ingreso con categoría y además ligado al evento (trade_id).
    op.drop_constraint(
        op.f("ck_transactions_category_transfer_or_trade"), "transactions", type_="check"
    )
    op.create_check_constraint(
        op.f("ck_transactions_movement_links"),
        "transactions",
        "(transfer_group_id IS NOT NULL) <> (num_nonnulls(category_id, trade_id) > 0)",
    )


def downgrade() -> None:
    # Falla si ya hay rentas registradas: borrarlas es decisión de quien hace el downgrade.
    op.drop_constraint(op.f("ck_transactions_movement_links"), "transactions", type_="check")
    op.create_check_constraint(
        op.f("ck_transactions_category_transfer_or_trade"),
        "transactions",
        "num_nonnulls(category_id, transfer_group_id, trade_id) = 1",
    )
