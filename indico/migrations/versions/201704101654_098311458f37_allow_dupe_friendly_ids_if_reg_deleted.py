"""Allow dupe friendly ids if reg deleted

Revision ID: 098311458f37
Revises: 0a249b3e9883
Create Date: 2017-04-10 16:54:19.811845
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '098311458f37'
down_revision = '0a249b3e9883'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('ix_uq_registrations_friendly_id_event_id', table_name='registrations', schema='event_registration')
    op.create_index(None, 'registrations', ['friendly_id', 'event_id'], unique=True,
                    postgresql_where=sa.text('NOT is_deleted'), schema='event_registration')


def downgrade():
    op.drop_index('ix_uq_registrations_friendly_id_event_id', table_name='registrations', schema='event_registration')
    op.create_index(None, 'registrations', ['friendly_id', 'event_id'], unique=True, schema='event_registration')
