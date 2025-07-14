"""Add app logs

Revision ID: b4ee48f3052c
Revises: f2518f111aa7
Create Date: 2025-04-24 16:27:44.822810
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime


# revision identifiers, used by Alembic.
revision = 'b4ee48f3052c'
down_revision = 'f2518f111aa7'
branch_labels = None
depends_on = None


class _AppLogRealm(int, Enum):
    system = 1
    admin = 2


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
        sa.Column('realm', PyIntEnum(_AppLogRealm), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='indico',
    )
    op.create_index(None, 'logs', ['meta'], unique=False, schema='indico', postgresql_using='gin')


def downgrade():
    op.drop_table('logs', schema='indico')
