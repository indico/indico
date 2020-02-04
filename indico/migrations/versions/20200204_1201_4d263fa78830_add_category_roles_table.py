"""Add category roles table

Revision ID: 4d263fa78830
Revises: 6a185fdcd4ee
Create Date: 2020-02-04 12:01:02.554724
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '4d263fa78830'
down_revision = '6a185fdcd4ee'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=False),
        sa.Index(None, 'category_id', 'code', unique=True),
        sa.CheckConstraint('code = upper(code)', name='uppercase_code'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.categories.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='categories'
    )
    op.create_table(
        'role_members',
        sa.Column('role_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['role_id'], ['categories.roles.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('role_id', 'user_id'),
        schema='categories'
    )


def downgrade():
    op.drop_table('role_members', schema='categories')
    op.drop_table('roles', schema='categories')
