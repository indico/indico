"""Make room attributes global

Revision ID: ec410be271df
Revises: 27c45c384d65
Create Date: 2018-10-25 11:48:39.958768
"""

import sqlalchemy as sa
from alembic import context, op


# revision identifiers, used by Alembic.
revision = 'ec410be271df'
down_revision = '27c45c384d65'
branch_labels = None
depends_on = None


def _make_names_unique():
    conn = op.get_bind()
    default_location_id = conn.execute('SELECT id FROM roombooking.locations WHERE is_default').scalar()
    if default_location_id is None:
        has_dupes = conn.execute('SELECT COUNT(DISTINCT name) != COUNT(name) FROM roombooking.room_attributes').scalar()
        if has_dupes:
            raise Exception('Please set a default location or remove attributes whose names are not unique '
                            'across locations')
        return
    res = conn.execute('''
        SELECT attr.id, attr.name, loc.name AS location
        FROM roombooking.room_attributes attr
        JOIN roombooking.locations loc ON (loc.id = attr.location_id)
        WHERE attr.location_id != %s
    ''', (default_location_id,))
    for row in res:
        conflict = conn.execute("SELECT COUNT(*) FROM roombooking.room_attributes WHERE id != %s AND name = %s",
                                (row.id, row.name)).scalar()
        if conflict:
            new_name = '{} ({})'.format(row.name, row.location)
            conn.execute('UPDATE roombooking.room_attributes SET name = %s WHERE id = %s', (new_name, row.id))


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    _make_names_unique()
    op.drop_index('ix_room_attributes_name', table_name='room_attributes', schema='roombooking')
    op.drop_constraint('uq_room_attributes_name_location_id', 'room_attributes', schema='roombooking')
    op.create_index(None, 'room_attributes', ['name'], unique=True, schema='roombooking')
    op.drop_column('room_attributes', 'location_id', schema='roombooking')
    op.drop_column('room_attributes', 'type', schema='roombooking')


def downgrade():
    if context.is_offline_mode():
        raise Exception('This downgrade is only possible in online mode')
    conn = op.get_bind()
    default_location_id = conn.execute('SELECT id FROM roombooking.locations WHERE is_default').scalar()
    if default_location_id is None:
        if conn.execute('SELECT COUNT(*) FROM roombooking.locations').scalar():
            raise Exception('Please set a default location')
    default_location = unicode(default_location_id) if default_location_id is not None else None
    op.add_column('room_attributes', sa.Column('location_id', sa.Integer(), nullable=False,
                                               server_default=default_location),
                  schema='roombooking')
    op.alter_column('room_attributes', 'location_id', server_default=None, schema='roombooking')
    op.add_column('room_attributes', sa.Column('type', sa.String(), nullable=False, server_default='str'),
                  schema='roombooking')
    op.alter_column('room_attributes', 'type', server_default=None, schema='roombooking')
    op.create_foreign_key(None, 'room_attributes', 'locations', ['location_id'], ['id'],
                          source_schema='roombooking', referent_schema='roombooking')
    op.drop_index('ix_uq_room_attributes_name', table_name='room_attributes', schema='roombooking')
    op.create_unique_constraint(None, 'room_attributes', ['name', 'location_id'], schema='roombooking')
    op.create_index(None, 'room_attributes', ['name'], schema='roombooking')
