"""Add user profile picture

Revision ID: 532f0ea25bb1
Revises: 7f56252c73ab
Create Date: 2020-04-28 18:07:51.879932
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '532f0ea25bb1'
down_revision = '7f56252c73ab'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('picture', sa.LargeBinary(), nullable=True), schema='users')
    op.add_column('users', sa.Column('picture_metadata', postgresql.JSONB(), nullable=False, server_default='null'),
                  schema='users')
    op.alter_column('users', 'picture_metadata', server_default=None, schema='users')
    op.create_check_constraint('valid_picture', 'users', "(picture IS NULL) = (picture_metadata::text = 'null')",
                               schema='users')


def downgrade():
    op.drop_column('users', 'picture_metadata', schema='users')
    op.drop_column('users', 'picture', schema='users')
