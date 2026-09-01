"""add archived status to quote status enum

Revision ID: 16606f01af36
Revises: 5de5ff38282d
Create Date: 2026-09-01 13:19:49.665647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16606f01af36'
down_revision: Union[str, Sequence[str], None] = '5de5ff38282d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # New enum labels can't be added inside a transaction block in Postgres.
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE quotestatus ADD VALUE IF NOT EXISTS 'archived'")
    # SQLite stores the column as a plain VARCHAR with no CHECK constraint,
    # so no schema change is needed there — see 5de5ff38282d.


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres cannot drop a single enum value without rebuilding the type;
    # not worth the risk for a low-volume internal tool. Reassign any
    # archived rows back to draft before downgrading if this is ever run.
    pass
