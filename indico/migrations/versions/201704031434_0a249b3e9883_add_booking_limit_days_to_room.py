"""Add booking_limit_days to Room

Revision ID: 0a249b3e9883
Revises: eb58b6e68c19
Create Date: 2017-03-15 15:52:04.558105
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '0a249b3e9883'
down_revision = 'eb58b6e68c19'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('rooms',
                  sa.Column('booking_limit_days', sa.Integer(), nullable=True),
                  schema='roombooking')


def downgrade():
    op.drop_column('rooms', 'booking_limit_days', schema='roombooking')
