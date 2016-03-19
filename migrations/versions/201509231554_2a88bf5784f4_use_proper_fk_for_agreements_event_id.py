"""Use proper FK for agreements event_id

Revision ID: 2a88bf5784f4
Revises: 2b0deec3a217
Create Date: 2015-09-23 15:54:31.927214
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '2a88bf5784f4'
down_revision = '2b0deec3a217'


def upgrade():
    # delete orphaned agreements. they are usually from test evens that
    # got deleted at some point
    op.execute("DELETE FROM events.agreements ea WHERE NOT EXISTS "
               "(SELECT 1 FROM events.events e WHERE e.id = ea.event_id)")
    op.create_index(None, 'agreements', ['event_id'], schema='events')
    op.create_foreign_key(None,
                          'agreements', 'events',
                          ['event_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_agreements_event_id_events'), 'agreements', schema='events')
    op.drop_index(op.f('ix_agreements_event_id'), table_name='agreements', schema='events')
