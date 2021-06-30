"""Add last_used_ip and use_count to tokens

Revision ID: 5cbb0eb12eb3
Revises: 1b7e98f581bc
Create Date: 2021-06-30 13:49:55.566636
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '5cbb0eb12eb3'
down_revision = '1b7e98f581bc'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tokens', sa.Column('last_used_ip', postgresql.INET(), nullable=True), schema='users')
    op.add_column('tokens', sa.Column('last_used_ip', postgresql.INET(), nullable=True), schema='oauth')
    op.add_column('tokens', sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'), schema='users')
    op.add_column('tokens', sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'), schema='oauth')
    op.alter_column('tokens', 'use_count', server_default=None, schema='users')
    op.alter_column('tokens', 'use_count', server_default=None, schema='oauth')


def downgrade():
    op.drop_column('tokens', 'last_used_ip', schema='users')
    op.drop_column('tokens', 'last_used_ip', schema='oauth')
    op.drop_column('tokens', 'use_count', schema='users')
    op.drop_column('tokens', 'use_count', schema='oauth')
