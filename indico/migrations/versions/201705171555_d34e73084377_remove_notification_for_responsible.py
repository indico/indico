"""Remove notification_for_responsible from Room

Revision ID: d34e73084377
Revises: 4d133b989dcb
Create Date: 2017-04-25 14:50:55.009889
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd34e73084377'
down_revision = '4d133b989dcb'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('rooms', 'notification_for_responsible', schema='roombooking')


def downgrade():
    op.add_column('rooms', sa.Column('notification_for_responsible', sa.Boolean(), nullable=False,
                                     server_default='false'), schema='roombooking')
    op.alter_column('rooms', 'notification_for_responsible', server_default=None, schema='roombooking')
