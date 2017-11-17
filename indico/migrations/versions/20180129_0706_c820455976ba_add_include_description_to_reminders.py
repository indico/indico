"""Add include_description to reminders

Revision ID: c820455976ba
Revises: 093533d27a96
Create Date: 2018-01-29 07:06:00.000000
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'c820455976ba'
down_revision = '093533d27a96'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reminders', sa.Column('include_description', sa.Boolean(), nullable=False,
                                         server_default='false'), schema='events')
    op.alter_column('reminders', 'include_description', server_default=None, schema='events')


def downgrade():
    op.drop_column('reminders', 'include_description', schema='events')
