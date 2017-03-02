"""Add event log entry table

Revision ID: 9f0a44f8035
Revises: 48177e1c4aa4
Create Date: 2015-06-11 14:36:32.203307
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.modules.events.logs.models.entries import EventLogKind, EventLogRealm


# revision identifiers, used by Alembic.
revision = '9f0a44f8035'
down_revision = '48177e1c4aa4'


def upgrade():
    op.create_table('logs',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('user_id', sa.Integer(), nullable=True, index=True),
                    sa.Column('logged_dt', UTCDateTime, nullable=False),
                    sa.Column('realm', PyIntEnum(EventLogRealm), nullable=False),
                    sa.Column('kind', PyIntEnum(EventLogKind), nullable=False),
                    sa.Column('module', sa.String(), nullable=False),
                    sa.Column('type', sa.String(), nullable=False),
                    sa.Column('summary', sa.String(), nullable=False),
                    sa.Column('data', postgresql.JSON(), nullable=False),
                    sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='events')


def downgrade():
    op.drop_table('logs', schema='events')
