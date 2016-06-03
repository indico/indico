"""Add favorite category FK

Revision ID: 2940c52467e4
Revises: 3032079d8b33
Create Date: 2016-06-03 13:23:10.249330
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '2940c52467e4'
down_revision = '3032079d8b33'


def upgrade():
    op.create_foreign_key(None,
                          'favorite_categories', 'categories',
                          ['target_id'], ['id'],
                          source_schema='users', referent_schema='categories')


def downgrade():
    op.drop_constraint('fk_favorite_categories_target_id_categories', 'favorite_categories', schema='users')
