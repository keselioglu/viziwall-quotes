"""fix quote status enum missing values on postgres

Revision ID: 2dfe782ec0e5
Revises: 0a91086ee666
Create Date: 2026-09-04 11:10:12.646058

The 5de5ff38282d migration used batch_alter_table().alter_column(type_=sa.Enum(...))
to expand the QuoteStatus enum. That correctly recreates the column on SQLite (where
batch mode rebuilds the table), but on Postgres it doesn't actually alter the enum
type's value set — only ALTER TYPE ... ADD VALUE does that. 16606f01af36 (the very
next migration) already worked around this correctly for 'archived'; this migration
applies the same fix for the rest of the values 5de5ff38282d was supposed to add,
which were silently never added to the real Postgres enum. Production's quotestatus
type was still ('draft', 'sent', 'accepted', 'rejected', 'expired', 'archived') —
missing 'follow_up_sent', 'new_version_sent', 'waiting', 'approved', 'declined',
'cancelled' — before this migration.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2dfe782ec0e5'
down_revision: Union[str, Sequence[str], None] = '0a91086ee666'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_VALUES = ['follow_up_sent', 'new_version_sent', 'waiting', 'approved', 'declined', 'cancelled']


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # New enum labels can't be added inside a transaction block in Postgres.
        with op.get_context().autocommit_block():
            for value in NEW_VALUES:
                op.execute(f"ALTER TYPE quotestatus ADD VALUE IF NOT EXISTS '{value}'")
    # SQLite stores the column as a plain VARCHAR with no CHECK constraint, so it
    # already accepts any of these values — no schema change needed there.


def downgrade() -> None:
    # Postgres cannot drop enum values without rebuilding the type; not worth the
    # risk for a low-volume internal tool, same call as 16606f01af36 made for
    # 'archived'. Reassign any rows using these statuses back to draft first if
    # this is ever run.
    pass
