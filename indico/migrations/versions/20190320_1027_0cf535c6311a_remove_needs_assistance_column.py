"""Remove room assistance related columns

Revision ID: 0cf535c6311a
Revises: fe73a07da0b4
Create Date: 2019-02-21 10:27:01.191633
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '0cf535c6311a'
down_revision = 'fe73a07da0b4'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('reservations', 'needs_assistance', schema='roombooking')
    op.drop_column('rooms', 'notification_for_assistance', schema='roombooking')


def downgrade():
    op.add_column('reservations',
                  sa.Column('needs_assistance', sa.Boolean(), nullable=False, server_default='false'),
                  schema='roombooking')
    op.alter_column('reservations', 'needs_assistance', server_default=None, schema='roombooking')
    op.add_column('rooms',
                  sa.Column('notification_for_assistance', sa.Boolean(), nullable=False, server_default='false'),
                  schema='roombooking')
    op.alter_column('rooms', 'notification_for_assistance', server_default=None, schema='roombooking')
