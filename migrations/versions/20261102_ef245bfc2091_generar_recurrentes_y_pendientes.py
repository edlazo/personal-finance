"""generar recurrentes y pendientes

Revision ID: ef245bfc2091
Revises: c7e181cff08d
Create Date: 2026-11-02 22:39:14.506419

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "ef245bfc2091"
down_revision: str | Sequence[str] | None = "c7e181cff08d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recurring_pending",
        sa.Column("rule_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["rule_id"],
            ["recurring_rules.id"],
            name=op.f("fk_recurring_pending_rule_id_recurring_rules"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_recurring_pending_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recurring_pending")),
        sa.UniqueConstraint("rule_id", "date", name=op.f("uq_recurring_pending_rule_id_date")),
    )
    op.create_index(
        op.f("ix_recurring_pending_user_id"), "recurring_pending", ["user_id"], unique=False
    )
    op.add_column(
        "recurring_rules",
        sa.Column("needs_confirmation", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column("recurring_rules", sa.Column("generated_until", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("recurring_rules", "generated_until")
    op.drop_column("recurring_rules", "needs_confirmation")
    op.drop_index(op.f("ix_recurring_pending_user_id"), table_name="recurring_pending")
    op.drop_table("recurring_pending")
