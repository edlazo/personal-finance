"""crear tabla de reglas recurrentes

Revision ID: c7e181cff08d
Revises: 4b256e91eccd
Create Date: 2026-11-02 20:02:07.753105

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c7e181cff08d"
down_revision: str | Sequence[str] | None = "4b256e91eccd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recurring_rules",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("INCOME", "EXPENSE", name="transaction_kind", native_enum=False, length=10),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column(
            "frequency",
            sa.Enum(
                "WEEKLY",
                "MONTHLY",
                "YEARLY",
                name="recurring_frequency",
                native_enum=False,
                length=10,
            ),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("paused", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name=op.f("fk_recurring_rules_account_id_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_recurring_rules_category_id_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_recurring_rules_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recurring_rules")),
    )
    op.create_index(
        op.f("ix_recurring_rules_account_id"), "recurring_rules", ["account_id"], unique=False
    )
    op.create_index(
        op.f("ix_recurring_rules_user_id"), "recurring_rules", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_recurring_rules_user_id"), table_name="recurring_rules")
    op.drop_index(op.f("ix_recurring_rules_account_id"), table_name="recurring_rules")
    op.drop_table("recurring_rules")
