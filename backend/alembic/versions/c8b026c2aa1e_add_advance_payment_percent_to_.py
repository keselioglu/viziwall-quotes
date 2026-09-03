"""add advance payment percent to quotations

Revision ID: c8b026c2aa1e
Revises: eb19c614d594
Create Date: 2026-09-03 16:25:54.687259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8b026c2aa1e'
down_revision: Union[str, Sequence[str], None] = 'eb19c614d594'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("quotations", schema=None) as batch_op:
        batch_op.add_column(sa.Column("advance_payment_percent", sa.Numeric(precision=5, scale=2), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("quotations", schema=None) as batch_op:
        batch_op.drop_column("advance_payment_percent")
