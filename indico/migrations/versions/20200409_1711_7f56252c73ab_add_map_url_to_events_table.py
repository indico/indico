"""Add map_url to events table

Revision ID: 7f56252c73ab
Revises: 933665578547
Create Date: 2020-04-09 17:11:13.685047
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '7f56252c73ab'
down_revision = '933665578547'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('events', sa.Column('map_url', sa.String(), nullable=False, server_default=''), schema='events')
    op.alter_column('events', 'map_url', server_default=None, schema='events')


def downgrade():
    op.drop_column('events', 'map_url', schema='events')
