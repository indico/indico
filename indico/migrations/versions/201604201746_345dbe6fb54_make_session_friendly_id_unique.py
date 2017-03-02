"""Make session friendly_id unique

Revision ID: 345dbe6fb54
Revises: 33eb26faf225
Create Date: 2016-04-20 17:46:12.933652
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '345dbe6fb54'
down_revision = '33eb26faf225'


def upgrade():
    op.create_index(None, 'sessions', ['friendly_id', 'event_id'], unique=True, schema='events')


def downgrade():
    op.drop_index('ix_uq_sessions_friendly_id_event_id', table_name='sessions', schema='events')
