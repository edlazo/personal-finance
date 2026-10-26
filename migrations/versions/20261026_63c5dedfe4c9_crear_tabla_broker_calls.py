"""crear tabla broker_calls

Revision ID: 63c5dedfe4c9
Revises: 92214b67a6db
Create Date: 2026-10-26 09:48:28.912941

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "63c5dedfe4c9"
down_revision: str | Sequence[str] | None = "92214b67a6db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "broker_calls",
        sa.Column(
            "broker", sa.Enum("IOL", name="broker", native_enum=False, length=10), nullable=False
        ),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("calls", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_broker_calls_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_broker_calls")),
        sa.UniqueConstraint(
            "user_id", "broker", "month", name=op.f("uq_broker_calls_user_id_broker_month")
        ),
    )
    op.create_index(op.f("ix_broker_calls_user_id"), "broker_calls", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_broker_calls_user_id"), table_name="broker_calls")
    op.drop_table("broker_calls")
