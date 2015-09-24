"""Use proper FK for vc room assoc event_id

Revision ID: c0438fae3ac
Revises: 326682f8465d
Create Date: 2015-09-24 11:42:18.128471
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'c0438fae3ac'
down_revision = '326682f8465d'


def upgrade():
    op.create_foreign_key(None,
                          'vc_room_events', 'events',
                          ['event_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_vc_room_events_event_id_events'), 'vc_room_events', schema='events')
