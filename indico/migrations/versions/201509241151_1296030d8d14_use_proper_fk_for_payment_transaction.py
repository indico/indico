"""Use proper FK for payment transaction event_id

Revision ID: 1296030d8d14
Revises: c0438fae3ac
Create Date: 2015-09-24 11:51:36.075052
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '1296030d8d14'
down_revision = 'c0438fae3ac'


def upgrade():
    # delete orphaned payment transactions (of events that were deleted before we had the events table)
    op.execute("DELETE FROM events.payment_transactions el WHERE NOT EXISTS "
               "(SELECT 1 FROM events.events e WHERE e.id = el.event_id)")
    op.create_foreign_key(None,
                          'payment_transactions', 'events',
                          ['event_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_payment_transactions_event_id_events'), 'payment_transactions', schema='events')
