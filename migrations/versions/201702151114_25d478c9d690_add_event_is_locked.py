"""Add event.is_locked

Revision ID: 25d478c9d690
Revises: 399ef1b54f18
Create Date: 2017-02-15 11:14:45.966946
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '25d478c9d690'
down_revision = '399ef1b54f18'


def upgrade():
    op.add_column('events', sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='false'),
                  schema='events')
    op.alter_column('events', 'is_locked', server_default=None, schema='events')


def downgrade():
    op.drop_column('events', 'is_locked', schema='events')
