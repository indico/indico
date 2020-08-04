"""Fix session friendly id index

Revision ID: 497c61b68050
Revises: 12fbf6af2367
Create Date: 2020-08-04 13:08:57.032172
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '497c61b68050'
down_revision = '12fbf6af2367'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('ix_uq_sessions_friendly_id_event_id', table_name='sessions', schema='events')
    op.create_index(None, 'sessions', ['friendly_id', 'event_id'], unique=True,
                    postgresql_where=sa.text('NOT is_deleted'), schema='events')


def downgrade():
    op.drop_index('ix_uq_sessions_friendly_id_event_id', table_name='sessions', schema='events')
    op.create_index(None, 'sessions', ['friendly_id', 'event_id'], unique=True, schema='events')
