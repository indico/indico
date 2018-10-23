"""Add room_name_format

Revision ID: 55893713f6b7
Revises: 93985a8c11ed
Create Date: 2018-10-23 10:51:55.999263
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '55893713f6b7'
down_revision = '93985a8c11ed'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('locations',
                  sa.Column('room_name_format', sa.String(), nullable=False, server_default='%1$s/%2$s-%3$s'),
                  schema='roombooking')
    op.alter_column('locations', 'room_name_format', server_default=None, schema='roombooking')


def downgrade():
    op.drop_column('locations', 'room_name_format', schema='roombooking')
