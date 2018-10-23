"""Rename aspects to map areas

Revision ID: c5c21246445a
Revises: 7a72d63acba9
Create Date: 2018-10-23 17:16:17.845624
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'c5c21246445a'
down_revision = '7a72d63acba9'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('aspects', 'map_areas', schema='roombooking')
    op.execute('''
        ALTER INDEX roombooking.ix_uq_aspects_is_default RENAME TO ix_uq_map_areas_is_default;
        ALTER SEQUENCE roombooking.aspects_id_seq RENAME TO map_areas_id_seq;
        ALTER TABLE roombooking.map_areas RENAME CONSTRAINT pk_aspects TO pk_map_areas;
    ''')


def downgrade():
    op.rename_table('map_areas', 'aspects', schema='roombooking')
    op.execute('''
        ALTER INDEX roombooking.ix_uq_map_areas_is_default RENAME TO ix_uq_aspects_is_default;
        ALTER SEQUENCE roombooking.map_areas_id_seq RENAME TO aspects_id_seq;
        ALTER TABLE roombooking.aspects RENAME CONSTRAINT pk_map_areas TO pk_aspects;
    ''')
