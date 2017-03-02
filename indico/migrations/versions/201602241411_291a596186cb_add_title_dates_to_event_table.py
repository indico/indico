"""Add title/dates to event table

Revision ID: 291a596186cb
Revises: 3e7a0c029abb
Create Date: 2016-02-24 14:11:23.842725
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '291a596186cb'
down_revision = '3e7a0c029abb'


def upgrade():
    op.add_column('events', sa.Column('start_dt', UTCDateTime, nullable=True), schema='events')
    op.add_column('events', sa.Column('end_dt', UTCDateTime, nullable=True), schema='events')
    op.add_column('events', sa.Column('timezone', sa.String(), nullable=True), schema='events')
    op.add_column('events', sa.Column('title', sa.String(), nullable=True), schema='events')
    op.add_column('events', sa.Column('description', sa.Text(), nullable=True), schema='events')
    op.create_index(None, 'events', ['end_dt'], schema='events')
    op.create_index(None, 'events', ['start_dt'], schema='events')
    op.create_index(op.f('ix_events_title_fts'), 'events', [sa.text("to_tsvector('simple', title)")], schema='events',
                    postgresql_using='gin')
    op.create_index(op.f('ix_events_start_dt_desc'), 'events', [sa.text('start_dt DESC')], schema='events')
    op.create_index(op.f('ix_events_end_dt_desc'), 'events', [sa.text('end_dt DESC')], schema='events')
    op.create_check_constraint('valid_dates', 'events', "end_dt >= start_dt", schema='events')
    op.create_check_constraint('valid_title', 'events', "title != ''", schema='events')


def downgrade():
    op.drop_column('events', 'description', schema='events')
    op.drop_column('events', 'title', schema='events')
    op.drop_column('events', 'timezone', schema='events')
    op.drop_column('events', 'end_dt', schema='events')
    op.drop_column('events', 'start_dt', schema='events')
