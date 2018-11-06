"""Make equipment types global

Revision ID: 27c45c384d65
Revises: 0117bd0fa784
Create Date: 2018-10-24 14:24:46.437709
"""

import sqlalchemy as sa
from alembic import context, op


# revision identifiers, used by Alembic.
revision = '27c45c384d65'
down_revision = '0117bd0fa784'
branch_labels = None
depends_on = None


def _make_names_unique():
    conn = op.get_bind()
    default_location_id = conn.execute('SELECT id FROM roombooking.locations WHERE is_default').scalar()
    if default_location_id is None:
        has_dupes = conn.execute('SELECT COUNT(DISTINCT name) != COUNT(name) FROM roombooking.equipment_types').scalar()
        if has_dupes:
            raise Exception('Please set a default location or remove equipment types whose names are not unique '
                            'across locations')
        return
    res = conn.execute('''
        SELECT eq.id, eq.name, loc.name AS location
        FROM roombooking.equipment_types eq
        JOIN roombooking.locations loc ON (loc.id = eq.location_id)
        WHERE eq.location_id != %s
    ''', (default_location_id,))
    for row in res:
        conflict = conn.execute("SELECT COUNT(*) FROM roombooking.equipment_types WHERE id != %s AND name = %s",
                                (row.id, row.name)).scalar()
        if conflict:
            new_name = '{} ({})'.format(row.name, row.location)
            conn.execute('UPDATE roombooking.equipment_types SET name = %s WHERE id = %s', (new_name, row.id))


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    _make_names_unique()
    op.drop_index('ix_equipment_types_name', table_name='equipment_types', schema='roombooking')
    op.drop_constraint('uq_equipment_types_name_location_id', 'equipment_types', schema='roombooking')
    op.create_index(None, 'equipment_types', ['name'], unique=True, schema='roombooking')
    op.drop_column('equipment_types', 'location_id', schema='roombooking')


def downgrade():
    if context.is_offline_mode():
        raise Exception('This downgrade is only possible in online mode')
    conn = op.get_bind()
    default_location_id = conn.execute('SELECT id FROM roombooking.locations WHERE is_default').scalar()
    if default_location_id is None:
        if conn.execute('SELECT COUNT(*) FROM roombooking.locations').scalar():
            raise Exception('Please set a default location')
    default_location = unicode(default_location_id) if default_location_id is not None else None
    op.add_column('equipment_types', sa.Column('location_id', sa.Integer(), nullable=False,
                                               server_default=default_location),
                  schema='roombooking')
    op.alter_column('equipment_types', 'location_id', server_default=None, schema='roombooking')
    op.create_foreign_key(None, 'equipment_types', 'locations', ['location_id'], ['id'],
                          source_schema='roombooking', referent_schema='roombooking')
    op.drop_index('ix_uq_equipment_types_name', table_name='equipment_types', schema='roombooking')
    op.create_unique_constraint(None, 'equipment_types', ['name', 'location_id'], schema='roombooking')
    op.create_index(None, 'equipment_types', ['name'], schema='roombooking')
