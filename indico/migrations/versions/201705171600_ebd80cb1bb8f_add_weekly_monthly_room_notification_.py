"""Add weekly/monthly room notification options

Revision ID: ebd80cb1bb8f
Revises: d34e73084377
Create Date: 2017-05-17 15:48:41.390278
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'ebd80cb1bb8f'
down_revision = 'd34e73084377'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('rooms', sa.Column('notification_before_days_monthly', sa.Integer(), nullable=True),
                  schema='roombooking')
    op.add_column('rooms', sa.Column('notification_before_days_weekly', sa.Integer(), nullable=True),
                  schema='roombooking')


def downgrade():
    op.drop_column('rooms', 'notification_before_days_weekly', schema='roombooking')
    op.drop_column('rooms', 'notification_before_days_monthly', schema='roombooking')
    op.execute("DELETE FROM indico.settings WHERE module = 'roombooking' AND name = 'notification_before_days_weekly'")
    op.execute("DELETE FROM indico.settings WHERE module = 'roombooking' AND name = 'notification_before_days_monthly'")
