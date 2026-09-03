"""add events table

Revision ID: eb19c614d594
Revises: 81ab57568b2f
Create Date: 2026-09-03 11:59:12.170075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb19c614d594'
down_revision: Union[str, Sequence[str], None] = '81ab57568b2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("venue", sa.String(), nullable=True),
        sa.Column("default_start_date", sa.Date(), nullable=True),
        sa.Column("default_end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("events")
