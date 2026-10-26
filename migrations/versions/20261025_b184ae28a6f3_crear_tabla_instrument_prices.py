"""crear tabla instrument_prices

Revision ID: b184ae28a6f3
Revises: 73b924ba3b1c
Create Date: 2026-10-25 23:39:36.065586

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b184ae28a6f3"
down_revision: str | Sequence[str] | None = "73b924ba3b1c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "instrument_prices",
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("price", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "source",
            sa.Enum("MANUAL", name="price_source", native_enum=False, length=10),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.id"],
            name=op.f("fk_instrument_prices_instrument_id_instruments"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_instrument_prices_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_instrument_prices")),
    )
    op.create_index(
        op.f("ix_instrument_prices_instrument_id"),
        "instrument_prices",
        ["instrument_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instrument_prices_user_id"), "instrument_prices", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_instrument_prices_user_id"), table_name="instrument_prices")
    op.drop_index(op.f("ix_instrument_prices_instrument_id"), table_name="instrument_prices")
    op.drop_table("instrument_prices")
