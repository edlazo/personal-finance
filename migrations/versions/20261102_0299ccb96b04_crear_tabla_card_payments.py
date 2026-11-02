"""crear tabla card_payments

Revision ID: 0299ccb96b04
Revises: f4ca89a17665
Create Date: 2026-11-02 09:35:56.112638

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0299ccb96b04"
down_revision: str | Sequence[str] | None = "f4ca89a17665"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "card_payments",
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("closing_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column(
            "currency", sa.Enum("ARS", "USD", name="currency", native_enum=False), nullable=False
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name=op.f("fk_card_payments_account_id_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["card_id"], ["credit_cards.id"], name=op.f("fk_card_payments_card_id_credit_cards")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_card_payments_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_card_payments")),
    )
    op.create_index(op.f("ix_card_payments_card_id"), "card_payments", ["card_id"], unique=False)
    op.create_index(op.f("ix_card_payments_user_id"), "card_payments", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_card_payments_user_id"), table_name="card_payments")
    op.drop_index(op.f("ix_card_payments_card_id"), table_name="card_payments")
    op.drop_table("card_payments")
