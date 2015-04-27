"""Add user settings table

Revision ID: ea996ba6a96
Revises: 17be284e4062
Create Date: 2015-03-23 18:01:58.988025
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'ea996ba6a96'
down_revision = '17be284e4062'


def upgrade():
    op.create_table('settings',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('module', sa.String(), nullable=False, index=True),
                    sa.Column('name', sa.String(), nullable=False, index=True),
                    sa.Column('value', postgresql.JSON(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
                    sa.CheckConstraint('module = lower(module)', name='lowercase_module'),
                    sa.CheckConstraint('name = lower(name)', name='lowercase_name'),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('user_id', 'module', 'name'),
                    schema='users')
    op.create_index(None, 'settings', ['user_id', 'module'], unique=False, schema='users')
    op.create_index(None, 'settings', ['user_id', 'module', 'name'], unique=False, schema='users')


def downgrade():
    op.drop_table('settings', schema='users')
