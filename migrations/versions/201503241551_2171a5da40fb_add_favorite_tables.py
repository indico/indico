"""Add favorite tables

Revision ID: 2171a5da40fb
Revises: ea996ba6a96
Create Date: 2015-03-24 15:51:53.625505
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '2171a5da40fb'
down_revision = 'ea996ba6a96'


def upgrade():
    op.create_table('favorite_users',
                    sa.Column('target_id', sa.Integer(), autoincrement=False, nullable=False),
                    sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
                    sa.ForeignKeyConstraint(['target_id'], ['users.users.id']),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('target_id', 'user_id'),
                    schema='users')
    op.create_table('favorite_categories',
                    sa.Column('target_id', sa.String(), nullable=False),
                    sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False, index=True),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('target_id', 'user_id'),
                    schema='users')


def downgrade():
    op.drop_table('favorite_categories', schema='users')
    op.drop_table('favorite_users', schema='users')
