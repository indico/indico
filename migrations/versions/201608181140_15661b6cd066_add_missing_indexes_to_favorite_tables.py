"""Add missing indexes to favorite tables

Revision ID: 15661b6cd066
Revises: 90e05643cf5
Create Date: 2016-08-19 15:49:13.645247
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '15661b6cd066'
down_revision = '90e05643cf5'


def upgrade():
    op.create_index(None, 'favorite_categories', ['target_id'], unique=False, schema='users')
    op.create_index(None, 'favorite_users', ['target_id'], unique=False, schema='users')


def downgrade():
    op.drop_index('ix_favorite_users_target_id', table_name='favorite_users', schema='users')
    op.drop_index('ix_favorite_categories_target_id', table_name='favorite_categories', schema='users')
