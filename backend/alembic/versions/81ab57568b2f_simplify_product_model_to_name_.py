"""simplify product model to name, description, unit, unit_price

Revision ID: 81ab57568b2f
Revises: 9e1646d51a02
Create Date: 2026-09-02 17:54:16.973242

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81ab57568b2f'
down_revision: Union[str, Sequence[str], None] = '9e1646d51a02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.alter_column("price_per_day", new_column_name="unit_price")
        batch_op.drop_column("pixel_pitch_mm")
        batch_op.drop_column("panel_width_mm")
        batch_op.drop_column("panel_height_mm")
        batch_op.drop_column("resolution_width_px")
        batch_op.drop_column("resolution_height_px")
        batch_op.drop_column("price_per_week")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.alter_column("unit_price", new_column_name="price_per_day")
        batch_op.add_column(sa.Column("pixel_pitch_mm", sa.Numeric(5, 2), nullable=True))
        batch_op.add_column(sa.Column("panel_width_mm", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("panel_height_mm", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("resolution_width_px", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("resolution_height_px", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("price_per_week", sa.Numeric(10, 2), nullable=True))
