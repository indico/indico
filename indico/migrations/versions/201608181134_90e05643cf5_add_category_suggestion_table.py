"""Add category suggestion table

Revision ID: 90e05643cf5
Revises: 1b66d038da46
Create Date: 2016-08-18 11:34:38.203873
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '90e05643cf5'
down_revision = '1b66d038da46'


def upgrade():
    op.create_table(
        'suggested_categories',
        sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
        sa.Column('category_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
        sa.Column('is_ignored', sa.Boolean(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.categories.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('user_id', 'category_id'),
        schema='users'
    )


def downgrade():
    op.drop_table('suggested_categories', schema='users')
