"""Use proper FK for settings event_id

Revision ID: 2b0deec3a217
Revises: 5826cb0b0444
Create Date: 2015-09-23 15:25:39.638886
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '2b0deec3a217'
down_revision = '5826cb0b0444'


def upgrade():
    op.create_foreign_key(None,
                          'settings', 'events',
                          ['event_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.create_foreign_key(None,
                          'settings_principals', 'events',
                          ['event_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_settings_event_id_events'), 'settings', schema='events')
    op.drop_constraint(op.f('fk_settings_principals_event_id_events'), 'settings_principals', schema='events')
