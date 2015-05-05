"""Ensure user merged_into_id != id

Revision ID: 2b4b4bce2165
Revises: 26b356f99ad3
Create Date: 2015-05-05 11:49:22.808125
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '2b4b4bce2165'
down_revision = '26b356f99ad3'


def upgrade():
    op.create_check_constraint('not_merged_self', 'users', 'id != merged_into_id', schema='users')


def downgrade():
    op.drop_constraint('ck_users_not_merged_self', 'users', schema='users')
