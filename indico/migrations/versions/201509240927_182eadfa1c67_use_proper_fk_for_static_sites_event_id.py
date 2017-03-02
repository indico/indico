"""Use proper FK for static sites event_id

Revision ID: 182eadfa1c67
Revises: 42584bafda89
Create Date: 2015-09-24 09:27:29.307134
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '182eadfa1c67'
down_revision = '42584bafda89'


def upgrade():
    op.create_index(None, 'static_sites', ['event_id'], schema='events')
    op.create_foreign_key(None,
                          'static_sites', 'events',
                          ['event_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_static_sites_event_id_events'), 'static_sites', schema='events')
    op.drop_index(op.f('ix_static_sites_event_id'), table_name='static_sites', schema='events')
