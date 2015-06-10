"""Add legacy event id mapping table

Revision ID: 513886dc5547
Revises: a2dfbb4b85c
Create Date: 2015-06-10 15:10:07.819063
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '513886dc5547'
down_revision = 'a2dfbb4b85c'


def upgrade():
    op.create_table('legacy_id_map',
                    sa.Column('legacy_event_id', sa.String(), nullable=False, index=True),
                    sa.Column('event_id', sa.Integer(), nullable=False, autoincrement=False),
                    sa.PrimaryKeyConstraint('legacy_event_id', 'event_id'),
                    schema='events')


def downgrade():
    op.drop_table('legacy_id_map', schema='events')
