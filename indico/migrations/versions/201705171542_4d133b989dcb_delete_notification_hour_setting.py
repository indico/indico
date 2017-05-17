"""Delete notification_hour setting

Revision ID: 4d133b989dcb
Revises: bc4e7682e7df
Create Date: 2017-05-17 15:42:53.553219
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '4d133b989dcb'
down_revision = 'bc4e7682e7df'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DELETE FROM indico.settings WHERE module = 'roombooking' AND name = 'notification_hour'")


def downgrade():
    pass
