"""Ensure non-pending users have names

Revision ID: 2bb9dc6f5c28
Revises: 2b4b4bce2165
Create Date: 2015-05-07 17:04:22.636066
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '2bb9dc6f5c28'
down_revision = '2b4b4bce2165'


def upgrade():
    op.create_check_constraint('not_pending_proper_names', 'users',
                               "is_pending OR (first_name != '' AND last_name != '')", schema='users')


def downgrade():
    op.drop_constraint('ck_users_not_pending_proper_names', 'users', schema='users')
