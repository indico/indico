"""Use proper FK for reservations event_id

Revision ID: 279c53149a19
Revises: 182eadfa1c67
Create Date: 2015-09-24 10:22:31.691378
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '279c53149a19'
down_revision = '182eadfa1c67'


def upgrade():
    # disassociate reservations referencing deleted events
    op.execute("UPDATE roombooking.reservations r SET event_id = NULL WHERE r.event_id IS NOT NULL AND NOT EXISTS "
               "(SELECT 1 FROM events.events e WHERE e.id = r.event_id)")
    op.create_foreign_key(None,
                          'reservations', 'events',
                          ['event_id'], ['id'],
                          source_schema='roombooking', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_reservations_event_id_events'), 'reservations', schema='roombooking')
