"""Add category logs

Revision ID: 4b097412a8d9
Revises: 1cec32e42f65
Create Date: 2021-08-02 15:14:03.522614
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime


# revision identifiers, used by Alembic.
revision = '4b097412a8d9'
down_revision = '1cec32e42f65'
branch_labels = None
depends_on = None


class _CategoryLogRealm(int, Enum):
    category = 1
    events = 2


class _LogKind(int, Enum):
    other = 1
    positive = 2
    change = 3
    negative = 4


def upgrade():
    op.create_table(
        'logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('logged_dt', UTCDateTime, nullable=False),
        sa.Column('kind', PyIntEnum(_LogKind), nullable=False),
        sa.Column('module', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('summary', sa.String(), nullable=False),
        sa.Column('data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False, index=True),
        sa.Column('realm', PyIntEnum(_CategoryLogRealm), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.categories.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='categories'
    )
    op.create_index(None, 'logs', ['meta'], unique=False, schema='categories', postgresql_using='gin')


def downgrade():
    op.drop_table('logs', schema='categories')
