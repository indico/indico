"""Make Event.creator_id NOT NULL

Revision ID: 482ad7b081b9
Revises: eb582b7b0e1
Create Date: 2015-09-16 13:25:01.563819
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '482ad7b081b9'
down_revision = 'eb582b7b0e1'


def upgrade():
    op.alter_column('events', 'creator_id', nullable=False, schema='events')


def downgrade():
    op.alter_column('events', 'creator_id', nullable=True, schema='events')
