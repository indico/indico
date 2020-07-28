"""Add menu_entries.registered_only column.

Revision ID: d89abffb0f63
Revises: 4f0b4dd412b5
Create Date: 2020-07-28 18:42:54.968880
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd89abffb0f63'
down_revision = '4f0b4dd412b5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('menu_entries', sa.Column('registered_only', sa.Boolean(), nullable=False, server_default='false'),
                  schema='events')
    op.alter_column('menu_entries', 'registered_only', server_default=None, schema='events')


def downgrade():
    op.drop_column('menu_entries', 'registered_only', schema='events')
