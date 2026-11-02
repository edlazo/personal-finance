"""crear tablas de deudas

Revision ID: 928071532254
Revises: 0299ccb96b04
Create Date: 2026-11-02 09:59:18.823099

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "928071532254"
down_revision: str | Sequence[str] | None = "0299ccb96b04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "debts",
        sa.Column("counterparty", sa.String(length=100), nullable=False),
        sa.Column(
            "direction",
            sa.Enum("OWED", "LENT", name="debt_direction", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "currency", sa.Enum("ARS", "USD", name="currency", native_enum=False), nullable=False
        ),
        sa.Column("principal", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("installments", sa.SmallInteger(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("annual_rate", sa.Numeric(precision=9, scale=4), nullable=True),
        sa.Column("fixed_installment", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_debts_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_debts")),
    )
    op.create_index(op.f("ix_debts_user_id"), "debts", ["user_id"], unique=False)
    op.create_table(
        "debt_installments",
        sa.Column("debt_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.SmallInteger(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("principal", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("interest", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["debt_id"],
            ["debts.id"],
            name=op.f("fk_debt_installments_debt_id_debts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_debt_installments_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_debt_installments")),
    )
    op.create_index(
        op.f("ix_debt_installments_debt_id"), "debt_installments", ["debt_id"], unique=False
    )
    op.create_index(
        op.f("ix_debt_installments_user_id"), "debt_installments", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_debt_installments_user_id"), table_name="debt_installments")
    op.drop_index(op.f("ix_debt_installments_debt_id"), table_name="debt_installments")
    op.drop_table("debt_installments")
    op.drop_index(op.f("ix_debts_user_id"), table_name="debts")
    op.drop_table("debts")
