"""Add access column to menu entries

Revision ID: ef7a8b2e6737
Revises: 3dafee32ba7d
Create Date: 2022-02-25 13:35:15.089546
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum


# revision identifiers, used by Alembic.
revision = 'ef7a8b2e6737'
down_revision = '82fb6c6ac6db'
branch_labels = None
depends_on = None


class _MenuEntryAccess(int, Enum):
    everyone = 1
    registered_participants = 2
    speakers = 3


def upgrade():
    op.add_column('menu_entries',
                  sa.Column('access', PyIntEnum(_MenuEntryAccess), server_default='1', nullable=False),
                  schema='events')
    op.alter_column('menu_entries', 'access', server_default=None, schema='events')
    op.execute('UPDATE events.menu_entries SET access = 2 WHERE registered_only')
    op.drop_column('menu_entries', 'registered_only', schema='events')


def downgrade():
    op.add_column('menu_entries',
                  sa.Column('registered_only', sa.Boolean(), server_default='false', nullable=False),
                  schema='events')
    op.alter_column('menu_entries', 'registered_only', server_default=None, schema='events')
    op.execute('UPDATE events.menu_entries SET registered_only = true WHERE access > 1')
    op.drop_column('menu_entries', 'access', schema='events')
