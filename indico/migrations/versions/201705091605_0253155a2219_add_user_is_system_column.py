"""Add user is_system column

Revision ID: 0253155a2219
Revises: bc4e7682e7df
Create Date: 2017-05-09 16:05:10.259320
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '0253155a2219'
down_revision = 'bc4e7682e7df'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'), schema='users')
    op.alter_column('users', 'is_system', server_default=None, schema='users')
    op.create_index(None, 'users', ['is_system'], unique=True, schema='users', postgresql_where=sa.text('is_system'))
    op.create_check_constraint('valid_system_user', 'users',
                               'NOT is_system OR (NOT is_blocked AND NOT is_pending AND NOT is_deleted)',
                               schema='users')


def downgrade():
    op.drop_constraint('ck_users_valid_system_user', 'users', schema='users')
    op.drop_index('ix_uq_users_is_system', table_name='users', schema='users')
    op.drop_column('users', 'is_system', schema='users')
