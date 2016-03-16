"""Add event cloned_from_id

Revision ID: 38ed666dda98
Revises: b09db13d8da
Create Date: 2016-03-08 16:17:39.294809
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '38ed666dda98'
down_revision = 'b09db13d8da'


def upgrade():
    op.add_column('events', sa.Column('cloned_from_id', sa.Integer(), nullable=True), schema='events')
    op.create_index(None, 'events', ['cloned_from_id'], schema='events')
    op.create_check_constraint('not_cloned_from_self', 'events', 'cloned_from_id != id', schema='events')
    op.create_foreign_key(None, 'events', 'events',
                          ['cloned_from_id'], ['id'],
                          source_schema='events',
                          referent_schema='events')


def downgrade():
    op.drop_constraint('ck_events_not_cloned_from_self', 'events', schema='events')
    op.drop_column('events', 'cloned_from_id', schema='events')
