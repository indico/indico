"""Remove RoomAttribute.is_required

Revision ID: 4f98f2f979c7
Revises: 7e03b2262e9e
Create Date: 2018-11-23 10:36:14.406211
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '4f98f2f979c7'
down_revision = '7e03b2262e9e'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('room_attributes', 'is_required', schema='roombooking')


def downgrade():
    op.add_column('room_attributes', sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
                  schema='roombooking')
    op.alter_column('room_attributes', 'is_required', server_default=None, schema='roombooking')
