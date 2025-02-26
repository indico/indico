"""Add user logs

Revision ID: 4615aff776e0
Revises: 3fbd5d4ffb11
Create Date: 2025-02-24 18:32:20.784460
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime


# revision identifiers, used by Alembic.
revision = '4615aff776e0'
down_revision = '3fbd5d4ffb11'
branch_labels = None
depends_on = None


class _UserLogRealm(int, Enum):
    user = 1
    management = 2


class _LogKind(int, Enum):
    other = 1
    positive = 2
    change = 3
    negative = 4


def upgrade():
    op.create_table('logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('logged_dt', UTCDateTime, nullable=False),
        sa.Column('kind', PyIntEnum(_LogKind), nullable=False),
        sa.Column('module', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('summary', sa.String(), nullable=False),
        sa.Column('data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('realm', PyIntEnum(_UserLogRealm), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.users.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='users'
    )
    op.create_index(None, 'logs', ['meta'], unique=False, schema='users', postgresql_using='gin')


def downgrade():
    op.drop_table('logs', schema='users')
