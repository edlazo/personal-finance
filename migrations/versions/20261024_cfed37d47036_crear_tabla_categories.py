"""crear tabla categories

Revision ID: cfed37d47036
Revises: 0512b4589bfe
Create Date: 2026-10-24 07:57:48.557509

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "cfed37d47036"
down_revision: str | Sequence[str] | None = "0512b4589bfe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("INCOME", "EXPENSE", name="category_kind", native_enum=False, length=10),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_categories_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
    )
    op.create_index(op.f("ix_categories_user_id"), "categories", ["user_id"], unique=False)
    op.create_index(
        "uq_categories_user_id_kind_name",
        "categories",
        ["user_id", "kind", sa.literal_column("lower(name)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_categories_user_id_kind_name", table_name="categories")
    op.drop_index(op.f("ix_categories_user_id"), table_name="categories")
    op.drop_table("categories")
