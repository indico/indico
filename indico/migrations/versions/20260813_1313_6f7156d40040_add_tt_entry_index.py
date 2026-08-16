"""Add column_index to timetable_entries

Revision ID: 6f7156d40040
Revises: 06a037da1ec6
Create Date: 2025-07-28 11:07:21.759240
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '6f7156d40040'
down_revision = '06a037da1ec6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('timetable_entries',
                  sa.Column('column_index', sa.Integer(), nullable=False, server_default=0),
                  schema='events')
    op.alter_column('timetable_entries', 'column_index', server_default=None, schema='events')


def downgrade():
    op.drop_column('timetable_entries', 'column_index', schema='events')
