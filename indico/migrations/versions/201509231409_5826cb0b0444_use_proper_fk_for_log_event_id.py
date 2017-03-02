"""Use proper FK for log event_id

Revision ID: 5826cb0b0444
Revises: 3f9ba0aaa35a
Create Date: 2015-09-23 14:09:20.944438
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '5826cb0b0444'
down_revision = '3f9ba0aaa35a'


def upgrade():
    # delete orphaned log entries (usually vc rooms that were deleted on
    # event deletion and resulted in an email being sent and logged)
    op.execute("DELETE FROM events.logs el WHERE NOT EXISTS (SELECT 1 FROM events.events e WHERE e.id = el.event_id)")
    op.create_foreign_key(None,
                          'logs', 'events',
                          ['event_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_logs_event_id_events'), 'logs', schema='events')
