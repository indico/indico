"""Add valid_login_num to User

Revision ID: da259a74e28
Revises: 23ef6a49ae28
Create Date: 2016-07-29 17:04:53.295174
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'da259a74e28'
down_revision = '23ef6a49ae28'


def upgrade():
    op.add_column('users', sa.Column('valid_login_num', sa.Integer(), nullable=False, server_default='0'),
            schema='users')
    op.alter_column('users', 'valid_login_num', server_default=None, schema='users')


def downgrade():
    op.drop_column('users', 'valid_login_num', schema='users')
