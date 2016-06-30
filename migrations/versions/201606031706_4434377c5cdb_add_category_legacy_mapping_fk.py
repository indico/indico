"""Add category legacy mapping FK

Revision ID: 4434377c5cdb
Revises: 2940c52467e4
Create Date: 2016-06-03 17:06:40.253047
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '4434377c5cdb'
down_revision = '2940c52467e4'


def upgrade():
    op.create_index(None, 'legacy_id_map', ['category_id'], schema='categories')
    op.create_foreign_key(None,
                          'legacy_id_map', 'categories',
                          ['category_id'], ['id'],
                          source_schema='categories', referent_schema='categories')


def downgrade():
    op.drop_constraint('fk_legacy_id_map_category_id_categories', 'legacy_id_map', schema='categories')
    op.drop_index('ix_legacy_id_map_category_id', 'categories', schema='categories')
