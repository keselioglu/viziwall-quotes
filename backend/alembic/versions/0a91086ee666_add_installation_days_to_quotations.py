"""add installation_days to quotations

Revision ID: 0a91086ee666
Revises: 4bf03bb9a2e5
Create Date: 2026-09-03 17:30:11.081445

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a91086ee666'
down_revision: Union[str, Sequence[str], None] = '4bf03bb9a2e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("quotations", schema=None) as batch_op:
        batch_op.add_column(sa.Column("installation_days", sa.Integer(), nullable=False, server_default="2"))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("quotations", schema=None) as batch_op:
        batch_op.drop_column("installation_days")
