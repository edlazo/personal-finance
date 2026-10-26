"""crear tabla credit_cards

Revision ID: bfa1fbe369c9
Revises: 63c5dedfe4c9
Create Date: 2026-10-26 10:44:33.195052

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "bfa1fbe369c9"
down_revision: str | Sequence[str] | None = "63c5dedfe4c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "credit_cards",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "network",
            sa.Enum(
                "VISA",
                "MASTERCARD",
                "AMEX",
                "CABAL",
                "NARANJA",
                name="card_network",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("closing_day", sa.SmallInteger(), nullable=False),
        sa.Column("due_day", sa.SmallInteger(), nullable=False),
        sa.Column("dual_currency", sa.Boolean(), nullable=False),
        sa.Column("limit", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_credit_cards_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_credit_cards")),
    )
    op.create_index(op.f("ix_credit_cards_user_id"), "credit_cards", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_credit_cards_user_id"), table_name="credit_cards")
    op.drop_table("credit_cards")
