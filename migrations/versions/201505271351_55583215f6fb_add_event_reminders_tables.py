"""Add event reminders tables

Revision ID: 55583215f6fb
Revises: 4e27c1f90362
Create Date: 2015-05-27 13:51:59.987272
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '55583215f6fb'
down_revision = '4e27c1f90362'


def upgrade():
    op.create_table('reminders',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False),
                    sa.Column('creator_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('created_dt', UTCDateTime, nullable=False),
                    sa.Column('scheduled_dt', UTCDateTime, nullable=False),
                    sa.Column('is_sent', sa.Boolean(), nullable=False),
                    sa.Column('event_start_delta', sa.Interval(), nullable=True),
                    sa.Column('recipients', postgresql.ARRAY(sa.String()), nullable=False),
                    sa.Column('send_to_participants', sa.Boolean(), nullable=False),
                    sa.Column('include_summary', sa.Boolean(), nullable=False),
                    sa.Column('reply_to_address', sa.String(), nullable=False),
                    sa.Column('message', sa.String(), nullable=False),
                    sa.ForeignKeyConstraint(['creator_id'], ['users.users.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='events')
    op.create_index(None, 'reminders', ['scheduled_dt'], schema='events', postgresql_where=sa.text('not is_sent'))


def downgrade():
    op.drop_table('reminders', schema='events')
