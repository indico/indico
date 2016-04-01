"""Use proper ids for vc room mappings

Revision ID: 221268863b45
Revises: 29232c09e58a
Create Date: 2016-03-18 14:35:45.542305
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '221268863b45'
down_revision = '29232c09e58a'


def upgrade():
    op.add_column('vc_room_events', sa.Column('contribution_id', sa.Integer(), nullable=True), schema='events')
    op.add_column('vc_room_events', sa.Column('linked_event_id', sa.Integer(), nullable=True), schema='events')
    op.add_column('vc_room_events', sa.Column('session_block_id', sa.Integer(), nullable=True), schema='events')
    op.create_index(None, 'vc_room_events', ['contribution_id'], schema='events')
    op.create_index(None, 'vc_room_events', ['linked_event_id'], schema='events')
    op.create_index(None, 'vc_room_events', ['session_block_id'], schema='events')
    op.create_foreign_key(None,
                          'vc_room_events', 'events',
                          ['linked_event_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.create_foreign_key(None,
                          'vc_room_events', 'contributions',
                          ['contribution_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.create_foreign_key(None,
                          'vc_room_events', 'session_blocks',
                          ['session_block_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_column('vc_room_events', 'session_block_id', schema='events')
    op.drop_column('vc_room_events', 'linked_event_id', schema='events')
    op.drop_column('vc_room_events', 'contribution_id', schema='events')
