"""crear tabla instrument_events

Revision ID: 460ed4245a7c
Revises: 545d408c04e8
Create Date: 2026-10-26 08:16:21.169666

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "460ed4245a7c"
down_revision: str | Sequence[str] | None = "545d408c04e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "instrument_events",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("DIVIDEND", "COUPON", "AMORTIZATION", name="event_kind", native_enum=False),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("nominal", sa.Numeric(precision=28, scale=8), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name=op.f("fk_instrument_events_account_id_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.id"],
            name=op.f("fk_instrument_events_instrument_id_instruments"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_instrument_events_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_instrument_events")),
    )
    op.create_index(
        op.f("ix_instrument_events_account_id"), "instrument_events", ["account_id"], unique=False
    )
    op.create_index(
        op.f("ix_instrument_events_instrument_id"),
        "instrument_events",
        ["instrument_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instrument_events_user_id"), "instrument_events", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_instrument_events_user_id"), table_name="instrument_events")
    op.drop_index(op.f("ix_instrument_events_instrument_id"), table_name="instrument_events")
    op.drop_index(op.f("ix_instrument_events_account_id"), table_name="instrument_events")
    op.drop_table("instrument_events")
