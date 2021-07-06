"""Add is_flat_view_enabled setting for categories

Revision ID: cd3fef2095b4
Revises: 420195768776
Create Date: 2021-07-05 17:26:06.426820
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'cd3fef2095b4'
down_revision = '420195768776'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('categories', sa.Column('is_flat_view_enabled', sa.Boolean(), nullable=False, server_default='false'),
                  schema='categories')
    op.alter_column('categories', 'is_flat_view_enabled', server_default=None, schema='categories')


def downgrade():
    op.drop_column('categories', 'is_flat_view_enabled', schema='categories')
