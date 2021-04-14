"""Add attach_ical to reminders

Revision ID: 26985db8ed12
Revises: e787389ca868
Create Date: 2021-02-11 16:13:25.061874
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '26985db8ed12'
down_revision = 'e787389ca868'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reminders', sa.Column('attach_ical', sa.Boolean(), nullable=False,
                  server_default='false'), schema='events')
    op.alter_column('reminders', 'attach_ical', server_default=None, schema='events')


def downgrade():
    op.drop_column('reminders', 'attach_ical', schema='events')
