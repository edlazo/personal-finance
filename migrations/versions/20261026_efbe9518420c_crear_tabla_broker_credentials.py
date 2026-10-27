"""crear tabla broker_credentials

Revision ID: efbe9518420c
Revises: 460ed4245a7c
Create Date: 2026-10-26 09:05:05.001366

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "efbe9518420c"
down_revision: str | Sequence[str] | None = "460ed4245a7c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "broker_credentials",
        sa.Column(
            "broker", sa.Enum("IOL", name="broker", native_enum=False, length=10), nullable=False
        ),
        sa.Column("username_hint", sa.String(length=10), nullable=False),
        sa.Column("secret", sa.LargeBinary(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_broker_credentials_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_broker_credentials")),
        sa.UniqueConstraint("user_id", "broker", name=op.f("uq_broker_credentials_user_id_broker")),
    )
    op.create_index(
        op.f("ix_broker_credentials_user_id"), "broker_credentials", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_broker_credentials_user_id"), table_name="broker_credentials")
    op.drop_table("broker_credentials")
