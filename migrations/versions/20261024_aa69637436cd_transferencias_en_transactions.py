"""transferencias en transactions

Revision ID: aa69637436cd
Revises: eb611740dff9
Create Date: 2026-10-24 20:30:28.070716

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "aa69637436cd"
down_revision: str | Sequence[str] | None = "eb611740dff9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("transfer_group_id", sa.Uuid(), nullable=True))
    op.alter_column("transactions", "category_id", existing_type=sa.UUID(), nullable=True)
    op.create_index(
        op.f("ix_transactions_transfer_group_id"),
        "transactions",
        ["transfer_group_id"],
        unique=False,
    )
    op.create_check_constraint(
        op.f("ck_transactions_category_or_transfer"),
        "transactions",
        "(category_id IS NULL) <> (transfer_group_id IS NULL)",
    )


def downgrade() -> None:
    # Falla si ya hay transferencias: borrarlas es decisión de quien hace el downgrade.
    op.drop_constraint(op.f("ck_transactions_category_or_transfer"), "transactions", type_="check")
    op.drop_index(op.f("ix_transactions_transfer_group_id"), table_name="transactions")
    op.alter_column("transactions", "category_id", existing_type=sa.UUID(), nullable=False)
    op.drop_column("transactions", "transfer_group_id")
