"""Use proper FK for reminder event_id

Revision ID: 3f9ba0aaa35a
Revises: 482ad7b081b9
Create Date: 2015-09-23 12:09:43.398405
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3f9ba0aaa35a'
down_revision = '482ad7b081b9'


def upgrade():
    op.create_index(None, 'reminders', ['event_id'], schema='events')
    op.create_foreign_key(None,
                          'reminders', 'events',
                          ['event_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_reminders_event_id_events'), 'reminders', schema='events')
    op.drop_index(op.f('ix_reminders_event_id'), table_name='reminders', schema='events')
