"""crear tabla de pagos de deudas

Revision ID: 4b256e91eccd
Revises: 928071532254
Create Date: 2026-11-02 14:42:07.111761

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4b256e91eccd"
down_revision: str | Sequence[str] | None = "928071532254"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "debt_payments",
        sa.Column("debt_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name=op.f("fk_debt_payments_account_id_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["debt_id"], ["debts.id"], name=op.f("fk_debt_payments_debt_id_debts")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_debt_payments_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_debt_payments")),
    )
    op.create_index(op.f("ix_debt_payments_debt_id"), "debt_payments", ["debt_id"], unique=False)
    op.create_index(op.f("ix_debt_payments_user_id"), "debt_payments", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_debt_payments_user_id"), table_name="debt_payments")
    op.drop_index(op.f("ix_debt_payments_debt_id"), table_name="debt_payments")
    op.drop_table("debt_payments")
