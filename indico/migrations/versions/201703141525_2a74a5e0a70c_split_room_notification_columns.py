"""Split room notification columns

Revision ID: 2a74a5e0a70c
Revises: e185a5089262
Create Date: 2017-03-14 15:25:27.317015
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '2a74a5e0a70c'
down_revision = 'e185a5089262'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('rooms', sa.Column('notification_before_repeating', sa.Integer(), nullable=True),
                  schema='roombooking')
    op.add_column('rooms', sa.Column('notification_before_single', sa.Integer(), nullable=True), schema='roombooking')
    op.drop_column('rooms', 'notification_before_days', schema='roombooking')
    op.execute("DELETE FROM indico.settings WHERE module = 'roombooking' AND name = 'notification_before_days'")


def downgrade():
    op.add_column('rooms', sa.Column('notification_before_days', sa.Integer(), nullable=True), schema='roombooking')
    op.drop_column('rooms', 'notification_before_single', schema='roombooking')
    op.drop_column('rooms', 'notification_before_repeating', schema='roombooking')
    op.execute("DELETE FROM indico.settings WHERE module = 'roombooking' AND name = 'notification_before_repeating'")
    op.execute("DELETE FROM indico.settings WHERE module = 'roombooking' AND name = 'notification_before_single'")
