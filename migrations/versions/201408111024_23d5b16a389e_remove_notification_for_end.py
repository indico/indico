"""Remove notification_for_end

Revision ID: 23d5b16a389e
Revises: 31393135cd63
Create Date: 2014-08-11 10:24:10.092940
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23d5b16a389e'
down_revision = '31393135cd63'


def upgrade():
    op.drop_column('rooms', 'notification_for_end')


def downgrade():
    op.add_column('rooms', sa.Column('notification_for_end', sa.Boolean(), nullable=False, server_default='false'))
