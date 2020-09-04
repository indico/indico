"""Add column for profile picture type to User

Revision ID: f37d509e221c
Revises: c997dc927fbc
Create Date: 2020-09-04 15:43:18.413156
"""

import sqlalchemy as sa
from alembic import context, op

from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.users.models.users import SelectedProfilePicture


# revision identifiers, used by Alembic.
revision = 'f37d509e221c'
down_revision = 'c997dc927fbc'
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    op.add_column('users', sa.Column('picture_source', PyIntEnum(SelectedProfilePicture), nullable=False, server_default='0'), schema='users')
    op.alter_column('users', 'picture_source', server_default=None, schema='users')
    op.execute('UPDATE users.users SET picture_source = 3 WHERE picture IS NOT NULL')


def downgrade():
    op.drop_column('users', 'picture_source', schema='users')
