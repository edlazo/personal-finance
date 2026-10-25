"""crear tabla fx_rates

Revision ID: b8d9aab32d68
Revises: aa69637436cd
Create Date: 2026-10-24 22:04:48.785956

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8d9aab32d68"
down_revision: str | Sequence[str] | None = "aa69637436cd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fx_rates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "type",
            sa.Enum(
                "MEP",
                "OFICIAL",
                "BLUE",
                "CCL",
                "CRIPTO",
                name="type",
                native_enum=False,
                length=10,
            ),
            nullable=False,
        ),
        sa.Column("buy", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("sell", sa.Numeric(precision=28, scale=10), nullable=False),
        sa.Column("quoted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "source",
            sa.Enum("API", "MANUAL", name="source", native_enum=False, length=10),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("source IN ('API', 'MANUAL')", name=op.f("ck_fx_rates_source")),
        sa.CheckConstraint(
            "type IN ('MEP', 'OFICIAL', 'BLUE', 'CCL', 'CRIPTO')", name=op.f("ck_fx_rates_type")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_fx_rates_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fx_rates")),
    )
    op.create_index("ix_fx_rates_type_quoted_at", "fx_rates", ["type", "quoted_at"], unique=False)
    op.create_index(op.f("ix_fx_rates_user_id"), "fx_rates", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_fx_rates_user_id"), table_name="fx_rates")
    op.drop_index("ix_fx_rates_type_quoted_at", table_name="fx_rates")
    op.drop_table("fx_rates")
