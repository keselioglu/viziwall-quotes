"""add contact name and email to quotations

Revision ID: 4bf03bb9a2e5
Revises: c8b026c2aa1e
Create Date: 2026-09-03 17:20:23.464085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4bf03bb9a2e5'
down_revision: Union[str, Sequence[str], None] = 'c8b026c2aa1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("quotations", schema=None) as batch_op:
        batch_op.add_column(sa.Column("contact_name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("contact_email", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("quotations", schema=None) as batch_op:
        batch_op.drop_column("contact_email")
        batch_op.drop_column("contact_name")
