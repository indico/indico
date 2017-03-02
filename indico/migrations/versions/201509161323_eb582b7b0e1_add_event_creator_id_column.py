"""Add Event.creator_id column

Revision ID: eb582b7b0e1
Revises: 699b4e79992
Create Date: 2015-09-16 13:23:03.939928
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'eb582b7b0e1'
down_revision = '699b4e79992'


def upgrade():
    op.add_column('events', sa.Column('creator_id', sa.Integer(), nullable=True), schema='events')
    op.create_foreign_key(None,
                          'events', 'users',
                          ['creator_id'], ['id'],
                          source_schema='events', referent_schema='users')


def downgrade():
    op.drop_column('events', 'creator_id', schema='events')
