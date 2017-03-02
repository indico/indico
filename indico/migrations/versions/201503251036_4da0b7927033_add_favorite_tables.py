"""Add favorite tables

Revision ID: 4da0b7927033
Revises: ea996ba6a96
Create Date: 2015-03-25 10:36:45.379134
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '4da0b7927033'
down_revision = 'ea996ba6a96'


def upgrade():
    op.create_table('favorite_users',
                    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('target_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['target_id'], ['users.users.id']),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('user_id', 'target_id'),
                    schema='users')
    op.create_table('favorite_categories',
                    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('target_id', sa.String(), nullable=False),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('user_id', 'target_id'),
                    schema='users')


def downgrade():
    op.drop_table('favorite_categories', schema='users')
    op.drop_table('favorite_users', schema='users')
