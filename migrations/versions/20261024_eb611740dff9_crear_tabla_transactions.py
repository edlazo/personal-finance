"""crear tabla transactions

Revision ID: eb611740dff9
Revises: 07c17bdcfdf2
Create Date: 2026-10-24 19:51:54.640428

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "eb611740dff9"
down_revision: str | Sequence[str] | None = "07c17bdcfdf2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("INCOME", "EXPENSE", name="transaction_kind", native_enum=False, length=10),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name=op.f("fk_transactions_account_id_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], name=op.f("fk_transactions_category_id_categories")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_transactions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
    )
    op.create_index(op.f("ix_transactions_account_id"), "transactions", ["account_id"])
    op.create_index(op.f("ix_transactions_category_id"), "transactions", ["category_id"])
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"])
    op.create_index("ix_transactions_user_id_date", "transactions", ["user_id", "date"])


def downgrade() -> None:
    op.drop_index("ix_transactions_user_id_date", table_name="transactions")
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_category_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_account_id"), table_name="transactions")
    op.drop_table("transactions")
