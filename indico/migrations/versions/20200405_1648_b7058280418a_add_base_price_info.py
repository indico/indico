"""Add base_price_info

Revision ID: b7058280418a
Revises: 620b312814f3
Create Date: 2020-04-05 16:48:55.885158
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b7058280418a'
down_revision = '620b312814f3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('registrations', sa.Column('base_price_info', sa.String(), nullable=True, server_default=''),
                  schema='event_registration')
    op.alter_column('registrations', 'base_price_info', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('registrations', 'base_price_info', schema='event_registration')
