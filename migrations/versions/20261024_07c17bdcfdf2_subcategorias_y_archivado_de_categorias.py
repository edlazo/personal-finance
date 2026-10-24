"""subcategorias y archivado de categorias

Revision ID: 07c17bdcfdf2
Revises: cfed37d47036
Create Date: 2026-10-24 08:04:13.864260

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "07c17bdcfdf2"
down_revision: str | Sequence[str] | None = "cfed37d47036"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("parent_id", sa.Uuid(), nullable=True))
    op.add_column("categories", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        op.f("fk_categories_parent_id_categories"),
        "categories",
        "categories",
        ["parent_id"],
        ["id"],
    )
    op.create_index(op.f("ix_categories_parent_id"), "categories", ["parent_id"], unique=False)
    op.drop_index("uq_categories_user_id_kind_name", table_name="categories")
    op.create_index(
        "uq_categories_user_id_kind_parent_id_name",
        "categories",
        ["user_id", "kind", "parent_id", sa.literal_column("lower(name)")],
        unique=True,
        postgresql_nulls_not_distinct=True,
        postgresql_where=sa.text("archived_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_categories_user_id_kind_parent_id_name",
        table_name="categories",
        postgresql_where=sa.text("archived_at IS NULL"),
    )
    op.create_index(
        "uq_categories_user_id_kind_name",
        "categories",
        ["user_id", "kind", sa.literal_column("lower(name)")],
        unique=True,
    )
    op.drop_index(op.f("ix_categories_parent_id"), table_name="categories")
    op.drop_constraint(op.f("fk_categories_parent_id_categories"), "categories", type_="foreignkey")
    op.drop_column("categories", "archived_at")
    op.drop_column("categories", "parent_id")
