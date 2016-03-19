"""Add index for events.creator_id

Revision ID: 105a2d606ff7
Revises: 134a1c372738
Create Date: 2015-11-23 11:24:52.402629
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '105a2d606ff7'
down_revision = '134a1c372738'


def upgrade():
    op.create_index(None, 'events', ['creator_id'], unique=False, schema='events')


def downgrade():
    op.drop_index('ix_events_creator_id', 'events', schema='events')
