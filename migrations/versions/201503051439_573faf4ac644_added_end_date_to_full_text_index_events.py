"""Added end_date to full text index events

Revision ID: 573faf4ac644
Revises: 49ac5164a65b
Create Date: 2015-03-05 14:39:54.718493
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '573faf4ac644'
down_revision = '49ac5164a65b'


def upgrade():
    op.alter_column('event_index', 'start_date', nullable=False, schema='events')
    op.create_index('ix_start_date', 'event_index', ['start_date'], schema='events')

    op.add_column('event_index',
                  sa.Column('end_date', sa.DateTime(), nullable=False, server_default='now()'),
                  schema='events')
    op.alter_column('event_index', 'end_date', server_default=None, schema='events')
    op.create_index('ix_end_date', 'event_index', ['end_date'], schema='events')


def downgrade():
    op.alter_column('event_index', 'start_date', nullable=True, schema='events')
    op.drop_index('ix_start_date', table_name='event_index', schema='events')

    op.drop_column('event_index', 'end_date', schema='events')
