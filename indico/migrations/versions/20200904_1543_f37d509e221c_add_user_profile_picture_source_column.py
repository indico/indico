"""Add column for profile picture type to User

Revision ID: f37d509e221c
Revises: c997dc927fbc
Create Date: 2020-09-04 15:43:18.413156
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op
from werkzeug.http import http_date

from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.date_time import now_utc


# revision identifiers, used by Alembic.
revision = 'f37d509e221c'
down_revision = 'c997dc927fbc'
branch_labels = None
depends_on = None


class _ProfilePictureSource(int, Enum):
    standard = 0
    identicon = 1
    gravatar = 2
    custom = 3


def upgrade():
    op.add_column('users',
                  sa.Column('picture_source', PyIntEnum(_ProfilePictureSource), nullable=False, server_default='0'),
                  schema='users')
    op.alter_column('users', 'picture_source', server_default=None, schema='users')
    op.execute('UPDATE users.users SET picture_source = 3 WHERE picture IS NOT NULL')
    op.execute('''
        UPDATE users.users
        SET picture_metadata = picture_metadata || '{"lastmod": "%s"}'::jsonb
        WHERE picture_source = 3 AND NOT (picture_metadata ? 'lastmod')
    ''' % http_date(now_utc()))


def downgrade():
    op.drop_column('users', 'picture_source', schema='users')
