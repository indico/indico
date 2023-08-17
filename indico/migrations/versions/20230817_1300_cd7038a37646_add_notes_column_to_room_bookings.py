"""Add internal_note column to room bookings

Revision ID: cd7038a37646
Revises: cb46beecbb93
Create Date: 2023-04-24 15:11:55.407209
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'cd7038a37646'
down_revision = 'cb46beecbb93'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reservations', sa.Column('internal_note', sa.Text(), nullable=False, server_default=''),
                  schema='roombooking')
    op.alter_column('reservations', 'internal_note', server_default=None, schema='roombooking')


def downgrade():
    op.drop_column('reservations', 'internal_note', schema='roombooking')
