"""Add location information to events

Revision ID: 212f3acb0b1f
Revises: 105a2d606ff7
Create Date: 2015-11-23 11:27:26.294340
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '212f3acb0b1f'
down_revision = '105a2d606ff7'


def upgrade():
    not_null_cols = ('address', 'venue_name', 'room_name')
    op.add_column('events', sa.Column('address', sa.Text(), nullable=False, server_default=''),
                  schema='events')
    op.add_column('events', sa.Column('venue_name', sa.String(), nullable=False, server_default=''),
                  schema='events')
    op.add_column('events', sa.Column('room_id', sa.Integer(), nullable=True),
                  schema='events')
    op.add_column('events', sa.Column('room_name', sa.String(), nullable=False, server_default=''),
                  schema='events')
    op.create_index(None, 'events', ['room_id'], unique=False, schema='events')
    for col in not_null_cols:
        op.alter_column('events', col, server_default=None, schema='events')
    op.create_check_constraint('no_custom_location_if_room', 'events',
                               "(room_id IS NULL) OR (venue_name = '' AND room_name = '')",
                               schema='events')
    op.create_foreign_key(None,
                          'events', 'rooms',
                          ['room_id'], ['id'],
                          source_schema='events', referent_schema='roombooking')


def downgrade():
    op.drop_constraint('ck_events_no_custom_location_if_room', 'events', schema='events')
    op.drop_column('events', 'room_name', schema='events')
    op.drop_column('events', 'room_id', schema='events')
    op.drop_column('events', 'venue_name', schema='events')
    op.drop_column('events', 'address', schema='events')
