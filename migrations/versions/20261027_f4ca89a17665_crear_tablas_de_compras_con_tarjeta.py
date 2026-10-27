"""crear tablas de compras con tarjeta

Revision ID: f4ca89a17665
Revises: bfa1fbe369c9
Create Date: 2026-10-27 19:52:33.067153

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f4ca89a17665"
down_revision: str | Sequence[str] | None = "bfa1fbe369c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "card_purchases",
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column(
            "currency", sa.Enum("ARS", "USD", name="currency", native_enum=False), nullable=False
        ),
        sa.Column("installments", sa.SmallInteger(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["card_id"], ["credit_cards.id"], name=op.f("fk_card_purchases_card_id_credit_cards")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_card_purchases_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_card_purchases")),
    )
    op.create_index(op.f("ix_card_purchases_card_id"), "card_purchases", ["card_id"], unique=False)
    op.create_index(op.f("ix_card_purchases_user_id"), "card_purchases", ["user_id"], unique=False)
    op.create_table(
        "card_installments",
        sa.Column("purchase_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.SmallInteger(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column(
            "currency", sa.Enum("ARS", "USD", name="currency", native_enum=False), nullable=False
        ),
        sa.Column("closing_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["card_id"], ["credit_cards.id"], name=op.f("fk_card_installments_card_id_credit_cards")
        ),
        sa.ForeignKeyConstraint(
            ["purchase_id"],
            ["card_purchases.id"],
            name=op.f("fk_card_installments_purchase_id_card_purchases"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_card_installments_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_card_installments")),
    )
    op.create_index(
        op.f("ix_card_installments_card_id"), "card_installments", ["card_id"], unique=False
    )
    op.create_index(
        op.f("ix_card_installments_purchase_id"), "card_installments", ["purchase_id"], unique=False
    )
    op.create_index(
        op.f("ix_card_installments_user_id"), "card_installments", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_card_installments_user_id"), table_name="card_installments")
    op.drop_index(op.f("ix_card_installments_purchase_id"), table_name="card_installments")
    op.drop_index(op.f("ix_card_installments_card_id"), table_name="card_installments")
    op.drop_table("card_installments")
    op.drop_index(op.f("ix_card_purchases_user_id"), table_name="card_purchases")
    op.drop_index(op.f("ix_card_purchases_card_id"), table_name="card_purchases")
    op.drop_table("card_purchases")
