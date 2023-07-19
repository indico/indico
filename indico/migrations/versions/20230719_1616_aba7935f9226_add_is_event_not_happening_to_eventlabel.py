"""Add is_event_not_happening to EventLabel

Revision ID: aba7935f9226
Revises: 9b3fc740b722
Create Date: 2023-07-19 16:16:57.538875
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'aba7935f9226'
down_revision = '9b3fc740b722'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('labels', sa.Column('is_event_not_happening', sa.Boolean(), server_default='false', nullable=False),
                  schema='events')
    op.alter_column('labels', 'is_event_not_happening', server_default=None, schema='events')


def downgrade():
    op.drop_column('labels', 'is_event_not_happening', schema='events')
