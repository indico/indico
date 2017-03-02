"""Use proper FK for legacy event mapping event_id

Revision ID: 326682f8465d
Revises: 279c53149a19
Create Date: 2015-09-24 11:37:50.218586
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '326682f8465d'
down_revision = '279c53149a19'


def upgrade():
    op.create_index(None, 'legacy_id_map', ['event_id'], schema='events')
    op.create_foreign_key(None,
                          'legacy_id_map', 'events',
                          ['event_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_legacy_id_map_event_id_events'), 'legacy_id_map', schema='events')
    op.drop_index(op.f('ix_legacy_id_map_event_id'), table_name='legacy_id_map', schema='events')
