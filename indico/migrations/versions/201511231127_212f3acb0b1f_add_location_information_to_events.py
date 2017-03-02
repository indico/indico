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
    op.create_unique_constraint(None, 'rooms', ['id', 'location_id'], schema='roombooking')
    not_null_cols = ('address', 'venue_name', 'room_name')
    op.add_column('events', sa.Column('address', sa.Text(), nullable=False, server_default=''),
                  schema='events')
    op.add_column('events', sa.Column('venue_id', sa.Integer(), nullable=True),
                  schema='events')
    op.add_column('events', sa.Column('venue_name', sa.String(), nullable=False, server_default=''),
                  schema='events')
    op.add_column('events', sa.Column('room_id', sa.Integer(), nullable=True),
                  schema='events')
    op.add_column('events', sa.Column('room_name', sa.String(), nullable=False, server_default=''),
                  schema='events')
    op.create_index(None, 'events', ['venue_id'], unique=False, schema='events')
    op.create_index(None, 'events', ['room_id'], unique=False, schema='events')
    for col in not_null_cols:
        op.alter_column('events', col, server_default=None, schema='events')
    op.create_check_constraint('no_custom_location_if_room', 'events',
                               "(room_id IS NULL) OR (venue_name = '' AND room_name = '')",
                               schema='events')
    op.create_check_constraint('no_venue_name_if_venue_id', 'events', "(venue_id IS NULL) OR (venue_name = '')",
                               schema='events')
    op.create_check_constraint('venue_id_if_room_id', 'events', "(room_id IS NULL) OR (venue_id IS NOT NULL)",
                               schema='events')
    op.create_foreign_key(None,
                          'events', 'rooms',
                          ['room_id'], ['id'],
                          source_schema='events', referent_schema='roombooking')
    op.create_foreign_key(None,
                          'events', 'locations',
                          ['venue_id'], ['id'],
                          source_schema='events', referent_schema='roombooking')
    op.create_foreign_key(None,
                          'events', 'rooms',
                          ['venue_id', 'room_id'], ['location_id', 'id'],
                          source_schema='events', referent_schema='roombooking')


def downgrade():
    op.drop_constraint('ck_events_venue_id_if_room_id', 'events', schema='events')
    op.drop_constraint('ck_events_no_venue_name_if_venue_id', 'events', schema='events')
    op.drop_constraint('ck_events_no_custom_location_if_room', 'events', schema='events')
    op.drop_column('events', 'room_name', schema='events')
    op.drop_column('events', 'room_id', schema='events')
    op.drop_column('events', 'venue_name', schema='events')
    op.drop_column('events', 'venue_id', schema='events')
    op.drop_column('events', 'address', schema='events')
    op.drop_constraint('uq_rooms_id_location_id', 'rooms', schema='roombooking')
