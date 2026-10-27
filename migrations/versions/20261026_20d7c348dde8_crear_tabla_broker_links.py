"""crear tabla broker_links

Revision ID: 20d7c348dde8
Revises: efbe9518420c
Create Date: 2026-10-26 09:37:11.967552

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20d7c348dde8"
down_revision: str | Sequence[str] | None = "efbe9518420c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "broker_links",
        sa.Column(
            "broker", sa.Enum("IOL", name="broker", native_enum=False, length=10), nullable=False
        ),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name=op.f("fk_broker_links_account_id_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_broker_links_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_broker_links")),
        sa.UniqueConstraint("user_id", "broker", name=op.f("uq_broker_links_user_id_broker")),
    )
    op.create_index(
        op.f("ix_broker_links_account_id"), "broker_links", ["account_id"], unique=False
    )
    op.create_index(op.f("ix_broker_links_user_id"), "broker_links", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_broker_links_user_id"), table_name="broker_links")
    op.drop_index(op.f("ix_broker_links_account_id"), table_name="broker_links")
    op.drop_table("broker_links")
