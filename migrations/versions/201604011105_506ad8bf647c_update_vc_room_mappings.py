"""Update vc room mappings

Revision ID: 506ad8bf647c
Revises: 221268863b45
Create Date: 2016-03-18 14:42:27.473555
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '506ad8bf647c'
down_revision = '221268863b45'


def upgrade():
    op.execute("""
        UPDATE events.vc_room_events SET linked_event_id = event_id WHERE link_type = 1 AND linked_event_id IS NULL;

        UPDATE events.vc_room_events x SET contribution_id = (
            SELECT contribution_id
            FROM events.legacy_contribution_id_map
            WHERE event_id = x.event_id AND legacy_contribution_id = x.link_id
        ) WHERE link_type = 2 AND contribution_id IS NULL;

        UPDATE events.vc_room_events x SET session_block_id = (
            SELECT session_block_id
            FROM events.legacy_session_block_id_map
            WHERE event_id = x.event_id AND (legacy_session_id || ':' || legacy_session_block_id) = x.link_id
        ) WHERE link_type = 3 AND session_block_id IS NULL;
    """)
    op.create_check_constraint('valid_event_link', 'vc_room_events',
                               'link_type != 1 OR (contribution_id IS NULL AND session_block_id IS NULL AND '
                               'linked_event_id IS NOT NULL)',
                               schema='events')
    op.create_check_constraint('valid_contribution_link', 'vc_room_events',
                               'link_type != 2 OR (linked_event_id IS NULL AND session_block_id IS NULL AND '
                               'contribution_id IS NOT NULL)',
                               schema='events')
    op.create_check_constraint('valid_block_link', 'vc_room_events',
                               'link_type != 3 OR (contribution_id IS NULL AND linked_event_id IS NULL AND '
                               'session_block_id IS NOT NULL)',
                               schema='events')
    op.drop_column('vc_room_events', 'link_id', schema='events')


def downgrade():
    op.drop_constraint('ck_vc_room_events_valid_event_link', 'vc_room_events', schema='events')
    op.drop_constraint('ck_vc_room_events_valid_contribution_link', 'vc_room_events', schema='events')
    op.drop_constraint('ck_vc_room_events_valid_block_link', 'vc_room_events', schema='events')
    op.add_column('vc_room_events', sa.Column('link_id', sa.String(), nullable=True), schema='events')
