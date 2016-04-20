"""Allow dupe friendly contrib ids if one is deleted

Revision ID: 3ca8e62e6c36
Revises: 345dbe6fb54
Create Date: 2016-04-20 17:48:03.859888
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '3ca8e62e6c36'
down_revision = '345dbe6fb54'


def upgrade():
    op.drop_index('ix_uq_contributions_friendly_id_event_id', table_name='contributions', schema='events')
    op.create_index(None, 'contributions', ['friendly_id', 'event_id'], unique=True,
                    postgresql_where=sa.text('NOT is_deleted'), schema='events')


def downgrade():
    op.drop_index('ix_uq_contributions_friendly_id_event_id', table_name='contributions', schema='events')
    op.create_index(None, 'contributions', ['friendly_id', 'event_id'], unique=True, schema='events')
