"""drop rental_days from quote line items

Revision ID: 9e1646d51a02
Revises: e1908a57cf4d
Create Date: 2026-09-02 12:08:25.825593

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e1646d51a02'
down_revision: Union[str, Sequence[str], None] = 'e1908a57cf4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("quote_line_items", schema=None) as batch_op:
        batch_op.drop_column("rental_days")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("quote_line_items", schema=None) as batch_op:
        batch_op.add_column(sa.Column("rental_days", sa.Integer(), nullable=True))
