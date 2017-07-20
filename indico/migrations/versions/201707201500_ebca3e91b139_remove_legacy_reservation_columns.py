"""Remove legacy reservation columns

Revision ID: ebca3e91b139
Revises: bbe2ac15f488
Create Date: 2017-07-20 15:00:55.340542
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'ebca3e91b139'
down_revision = 'bbe2ac15f488'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('reservations', 'contact_phone', schema='roombooking')
    op.drop_column('reservations', 'contact_email', schema='roombooking')


def downgrade():
    op.add_column('reservations', sa.Column('contact_email', sa.String(), nullable=False, server_default=''),
                  schema='roombooking')
    op.add_column('reservations', sa.Column('contact_phone', sa.String(), nullable=False, server_default=''),
                  schema='roombooking')
    op.alter_column('reservations', 'contact_email', server_default=None, schema='roombooking')
    op.alter_column('reservations', 'contact_phone', server_default=None, schema='roombooking')
