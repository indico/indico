"""Add event created_dt

Revision ID: 35a6ae289e03
Revises: 3bdd6bf0181a
Create Date: 2016-06-24 14:15:23.459355
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '35a6ae289e03'
down_revision = '3bdd6bf0181a'


def upgrade():
    op.add_column('events', sa.Column('created_dt', UTCDateTime, nullable=True),
                  schema='events')
    op.execute('UPDATE events.events SET created_dt = start_dt')
    op.alter_column('events', 'created_dt', nullable=False, schema='events')
    op.create_index(None, 'events', ['created_dt'], schema='events')


def downgrade():
    op.drop_column('events', 'created_dt', schema='events')
