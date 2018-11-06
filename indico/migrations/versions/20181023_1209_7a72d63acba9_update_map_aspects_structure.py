"""Update map aspects structure

Revision ID: 7a72d63acba9
Revises: c0888cb57c58
Create Date: 2018-10-23 12:09:08.467153
"""

import sqlalchemy as sa
from alembic import context, op


# revision identifiers, used by Alembic.
revision = '7a72d63acba9'
down_revision = 'c0888cb57c58'
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    default_aspect_id = conn.execute('SELECT default_aspect_id FROM roombooking.locations WHERE is_default').scalar()
    op.add_column('aspects', sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
                  schema='roombooking')
    op.alter_column('aspects', 'is_default', server_default=None, schema='roombooking')
    op.alter_column('aspects', 'top_left_latitude', type_=sa.Float, schema='roombooking',
                    postgresql_using='top_left_latitude::double precision')
    op.alter_column('aspects', 'top_left_longitude', type_=sa.Float, schema='roombooking',
                    postgresql_using='top_left_longitude::double precision')
    op.alter_column('aspects', 'bottom_right_latitude', type_=sa.Float, schema='roombooking',
                    postgresql_using='bottom_right_latitude::double precision')
    op.alter_column('aspects', 'bottom_right_longitude', type_=sa.Float, schema='roombooking',
                    postgresql_using='bottom_right_longitude::double precision')
    op.create_index(None, 'aspects', ['is_default'], unique=True, schema='roombooking',
                    postgresql_where=sa.text('is_default'))
    op.drop_column('aspects', 'center_latitude', schema='roombooking')
    op.drop_column('aspects', 'location_id', schema='roombooking')
    op.drop_column('aspects', 'zoom_level', schema='roombooking')
    op.drop_column('aspects', 'center_longitude', schema='roombooking')
    op.drop_column('locations', 'default_aspect_id', schema='roombooking')
    if default_aspect_id is not None:
        conn.execute('UPDATE roombooking.aspects SET is_default = true WHERE id = %s', (default_aspect_id,))


def downgrade():
    if context.is_offline_mode():
        raise Exception('This downgrade is only possible in online mode')
    conn = op.get_bind()
    default_location_id = conn.execute('SELECT id FROM roombooking.locations WHERE is_default').scalar()
    if default_location_id is None:
        # We have some aspects that cannot be associated with a location since there is none
        conn.execute('DELETE FROM roombooking.aspects')
    default_location = unicode(default_location_id) if default_location_id is not None else None
    default_aspect_id = conn.execute('SELECT id FROM roombooking.aspects WHERE is_default').scalar()
    op.add_column('locations', sa.Column('default_aspect_id', sa.Integer, nullable=True), schema='roombooking')
    op.create_foreign_key(op.f('fk_locations_default_aspect_id'), 'locations', 'aspects',
                          ['default_aspect_id'], ['id'],
                          source_schema='roombooking', referent_schema='roombooking',
                          onupdate='CASCADE', ondelete='SET NULL')
    op.alter_column('aspects', 'top_left_latitude', type_=sa.String, schema='roombooking')
    op.alter_column('aspects', 'top_left_longitude', type_=sa.String, schema='roombooking')
    op.alter_column('aspects', 'bottom_right_latitude', type_=sa.String, schema='roombooking')
    op.alter_column('aspects', 'bottom_right_longitude', type_=sa.String, schema='roombooking')
    op.add_column('aspects', sa.Column('center_longitude', sa.String, nullable=False, server_default='0'),
                  schema='roombooking')
    op.alter_column('aspects', 'center_longitude', server_default=None, schema='roombooking')
    op.add_column('aspects', sa.Column('center_latitude', sa.String, nullable=False, server_default='0'),
                  schema='roombooking')
    op.alter_column('aspects', 'center_latitude', server_default=None, schema='roombooking')
    op.add_column('aspects', sa.Column('zoom_level', sa.SmallInteger, nullable=False, server_default='0'),
                  schema='roombooking')
    op.alter_column('aspects', 'zoom_level', server_default=None, schema='roombooking')
    op.add_column('aspects', sa.Column('location_id', sa.Integer, nullable=False, server_default=default_location),
                  schema='roombooking')
    op.alter_column('aspects', 'location_id', server_default=None, schema='roombooking')
    op.create_foreign_key(None, 'aspects', 'locations', ['location_id'], ['id'],
                          source_schema='roombooking', referent_schema='roombooking')
    op.drop_index('ix_uq_aspects_is_default', table_name='aspects', schema='roombooking')
    op.drop_column('aspects', 'is_default', schema='roombooking')
    if default_aspect_id is not None:
        conn.execute('UPDATE roombooking.locations SET default_aspect_id = %s WHERE id = %s',
                     (default_aspect_id, default_location_id))
