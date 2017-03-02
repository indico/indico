"""Use proper FK for requests event_id

Revision ID: 42584bafda89
Revises: 2a88bf5784f4
Create Date: 2015-09-23 17:58:18.705315
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '42584bafda89'
down_revision = '2a88bf5784f4'


def upgrade():
    op.create_foreign_key(None,
                          'requests', 'events',
                          ['event_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_requests_event_id_events'), 'requests', schema='events')
