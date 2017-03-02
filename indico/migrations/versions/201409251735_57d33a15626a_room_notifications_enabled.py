"""Add room notifications_enabled

Revision ID: 57d33a15626a
Revises: 1ae8ebf4bf79
Create Date: 2014-09-25 17:35:53.944817
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '57d33a15626a'
down_revision = '1ae8ebf4bf79'


def upgrade():
    op.add_column('rooms', sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default='true'),
                  schema='roombooking')
    op.alter_column('rooms', 'notifications_enabled', server_default=None, schema='roombooking')


def downgrade():
    op.drop_column('rooms', 'notifications_enabled', schema='roombooking')
