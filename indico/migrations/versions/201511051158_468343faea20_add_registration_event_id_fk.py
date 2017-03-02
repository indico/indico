"""Add Registration.event_id FK

Revision ID: 468343faea20
Revises: 2f4eefa1050c
Create Date: 2015-11-05 11:58:35.121858
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '468343faea20'
down_revision = '2f4eefa1050c'


def upgrade():
    op.create_foreign_key(None,
                          'registrations', 'events',
                          ['event_id'], ['id'],
                          source_schema='event_registration', referent_schema='events')


def downgrade():
    op.drop_constraint('fk_registrations_event_id_events', 'registrations', schema='event_registration')
