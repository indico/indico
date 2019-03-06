"""Add end notifications

Revision ID: 081d4c97060a
Revises: 7aabedfb5e3a
Create Date: 2019-02-27 15:23:31.582776
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '081d4c97060a'
down_revision = '7aabedfb5e3a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reservations',
                  sa.Column('end_notification_sent', sa.Boolean(), nullable=False, server_default='false'),
                  schema='roombooking')
    op.alter_column('reservations', 'end_notification_sent', server_default=None, schema='roombooking')
    op.add_column('rooms', sa.Column('end_notification_daily', sa.Integer()), schema='roombooking')
    op.add_column('rooms', sa.Column('end_notification_weekly', sa.Integer()), schema='roombooking')
    op.add_column('rooms', sa.Column('end_notification_monthly', sa.Integer()), schema='roombooking')
    op.add_column('rooms',
                  sa.Column('end_notifications_enabled', sa.Boolean(), nullable=False, server_default='true'),
                  schema='roombooking')
    op.alter_column('rooms', 'end_notifications_enabled', server_default=None, schema='roombooking')


def downgrade():
    op.drop_column('reservations', 'end_notification_sent', schema='roombooking')
    op.drop_column('rooms', 'end_notification_daily', schema='roombooking')
    op.drop_column('rooms', 'end_notification_weekly', schema='roombooking')
    op.drop_column('rooms', 'end_notification_monthly', schema='roombooking')
    op.drop_column('rooms', 'end_notifications_enabled', schema='roombooking')
