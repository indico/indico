"""rename IndexedEvent table to Event

Revision ID: 365fe2261342
Revises: 3778dc365e54
Create Date: 2015-08-05 15:18:10.748257
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '365fe2261342'
down_revision = '3778dc365e54'


def upgrade():
    op.drop_index('ix_event_index_end_date', table_name='event_index', schema='events')
    op.drop_index('ix_event_index_start_date', table_name='event_index', schema='events')
    op.drop_index('ix_event_index_title_vector', table_name='event_index', schema='events')

    op.rename_table('event_index', 'events', schema='events')
    op.create_index(op.f('ix_events_end_date'), 'events', ['end_date'], unique=False, schema='events')
    op.create_index(op.f('ix_events_start_date'), 'events', ['start_date'], unique=False, schema='events')
    op.create_index(op.f('ix_events_title_vector'), 'events', ['title_vector'], unique=False, schema='events',
                    postgresql_using='gin')

    op.add_column('events', sa.Column('logo', sa.LargeBinary(), nullable=True), schema='events')
    op.add_column('events', sa.Column('logo_metadata', postgresql.JSON(), nullable=True), schema='events')


def downgrade():
    op.drop_column('events', 'logo', schema='events')
    op.drop_column('events', 'logo_metadata', schema='events')
    op.drop_index(op.f('ix_events_title_vector'), table_name='events', schema='events')
    op.drop_index(op.f('ix_events_start_date'), table_name='events', schema='events')
    op.drop_index(op.f('ix_events_end_date'), table_name='events', schema='events')

    op.rename_table('events', 'event_index', schema='events')

    op.create_index('ix_event_index_title_vector', 'event_index', ['title_vector'], unique=False, schema='events')
    op.create_index('ix_event_index_start_date', 'event_index', ['start_date'], unique=False, schema='events')
    op.create_index('ix_event_index_end_date', 'event_index', ['end_date'], unique=False, schema='events')
