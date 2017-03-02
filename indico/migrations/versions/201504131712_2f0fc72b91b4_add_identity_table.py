"""Add identity table

Revision ID: 2f0fc72b91b4
Revises: 3463dd63745c
Create Date: 2015-04-13 17:12:37.264458
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '2f0fc72b91b4'
down_revision = '3463dd63745c'


def upgrade():
    op.create_table('identities',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('provider', sa.String(), nullable=False),
                    sa.Column('identifier', sa.String(), nullable=False),
                    sa.Column('multipass_data', postgresql.JSON(), nullable=False),
                    sa.Column('data', postgresql.JSON(), nullable=False),
                    sa.Column('password_hash', sa.String(), nullable=True),
                    sa.Column('last_login_dt', UTCDateTime, nullable=True),
                    sa.Column('last_login_ip', postgresql.INET(), nullable=True),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('provider', 'identifier'),
                    schema='users')


def downgrade():
    op.drop_table('identities', schema='users')
