"""Delete obsolete menu entries

Revision ID: 172df07a4f62
Revises: 8b5ab7da2d5
Create Date: 2016-11-10 14:34:09.111672
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '172df07a4f62'
down_revision = '8b5ab7da2d5'


def upgrade():
    op.execute("""
        DELETE FROM events.menu_entries
        WHERE type = 2 AND name IN ('my_tracks', 'program_my_tracks', 'abstract_submission')
    """)


def downgrade():
    pass
