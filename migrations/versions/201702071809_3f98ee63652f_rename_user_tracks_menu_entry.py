"""Rename user_tracks menu entry

Revision ID: 3f98ee63652f
Revises: 431e3a9178ab
Create Date: 2017-02-07 18:09:41.464183
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3f98ee63652f'
down_revision = '431e3a9178ab'


def upgrade():
    op.execute("""
        UPDATE events.menu_entries SET name = 'abstract_reviewing_area'
        WHERE type = 2 AND name = 'user_tracks'
    """)


def downgrade():
    pass
