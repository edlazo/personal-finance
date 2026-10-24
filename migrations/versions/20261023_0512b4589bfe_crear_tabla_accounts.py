"""crear tabla accounts

Revision ID: 0512b4589bfe
Revises: 3eae376b1bb6
Create Date: 2026-10-23 23:44:31.057594

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0512b4589bfe"
down_revision: str | Sequence[str] | None = "3eae376b1bb6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "SAVINGS",
                "CASH",
                "WALLET",
                "BROKER",
                "CRYPTO_WALLET",
                name="account_type",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column(
            "currency", sa.Enum("ARS", "USD", name="currency", native_enum=False), nullable=False
        ),
        sa.Column("initial_balance", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_accounts_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts")),
    )
    op.create_index(op.f("ix_accounts_user_id"), "accounts", ["user_id"], unique=False)
    op.create_index(
        "uq_accounts_user_id_active_name",
        "accounts",
        ["user_id", sa.literal_column("lower(name)")],
        unique=True,
        postgresql_where=sa.text("archived_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_accounts_user_id_active_name",
        table_name="accounts",
        postgresql_where=sa.text("archived_at IS NULL"),
    )
    op.drop_index(op.f("ix_accounts_user_id"), table_name="accounts")
    op.drop_table("accounts")
