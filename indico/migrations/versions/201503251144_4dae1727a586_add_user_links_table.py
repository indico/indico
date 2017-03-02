"""Add user links table

Revision ID: 4dae1727a586
Revises: 4da0b7927033
Create Date: 2015-03-25 11:44:12.413562
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '4dae1727a586'
down_revision = '4da0b7927033'


def upgrade():
    op.create_table('links',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('type', sa.String(), nullable=False),
                    sa.Column('role', sa.String(), nullable=False),
                    sa.Column('data', postgresql.JSON(), nullable=False),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='users')
    op.create_index(None, 'links', ['user_id', 'type', 'role'], unique=False, schema='users')


def downgrade():
    op.drop_table('links', schema='users')
