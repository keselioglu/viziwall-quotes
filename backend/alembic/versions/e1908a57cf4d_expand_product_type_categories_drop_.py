"""expand product type categories, drop logistics

Revision ID: e1908a57cf4d
Revises: 16606f01af36
Create Date: 2026-09-02 11:56:16.314458

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1908a57cf4d'
down_revision: Union[str, Sequence[str], None] = '16606f01af36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


new_values = ("led_wall", "displays", "audio", "it_equipment", "services")
old_values = ("led_wall", "logistics")


def upgrade() -> None:
    """Upgrade schema."""
    # Clearing the table first means the enum rebuild doesn't need to remap
    # any existing rows — the full catalog is being replaced in this release.
    op.execute("DELETE FROM products")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE producttype RENAME TO producttype_old")
        new_enum = sa.Enum(*new_values, name="producttype")
        new_enum.create(bind)
        with op.batch_alter_table("products", schema=None) as batch_op:
            batch_op.alter_column(
                "product_type",
                type_=new_enum,
                postgresql_using="product_type::text::producttype",
            )
        op.execute("DROP TYPE producttype_old")
    else:
        with op.batch_alter_table("products", schema=None) as batch_op:
            batch_op.alter_column("product_type", type_=sa.Enum(*new_values, name="producttype"))


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM products")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE producttype RENAME TO producttype_new")
        old_enum = sa.Enum(*old_values, name="producttype")
        old_enum.create(bind)
        with op.batch_alter_table("products", schema=None) as batch_op:
            batch_op.alter_column(
                "product_type",
                type_=old_enum,
                postgresql_using="product_type::text::producttype",
            )
        op.execute("DROP TYPE producttype_new")
    else:
        with op.batch_alter_table("products", schema=None) as batch_op:
            batch_op.alter_column("product_type", type_=sa.Enum(*old_values, name="producttype"))
