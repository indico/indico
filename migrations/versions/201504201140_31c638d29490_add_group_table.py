"""Add group table

Revision ID: 31c638d29490
Revises: 2f0fc72b91b4
Create Date: 2015-04-20 11:40:30.272456
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '31c638d29490'
down_revision = '2f0fc72b91b4'


def upgrade():
    op.create_table('groups',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False, index=True),
                    sa.PrimaryKeyConstraint('id'),
                    schema='users')
    op.create_index(op.f('ix_uq_groups_name_lower'), 'groups', [sa.text('lower(name)')], unique=True, schema='users')
    op.create_table('group_members',
                    sa.Column('group_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
                    sa.ForeignKeyConstraint(['group_id'], ['users.groups.id']),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('group_id', 'user_id'),
                    schema='users')


def downgrade():
    op.drop_table('group_members', schema='users')
    op.drop_table('groups', schema='users')
