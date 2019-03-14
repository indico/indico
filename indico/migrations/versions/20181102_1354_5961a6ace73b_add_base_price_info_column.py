"""Add base_price_info column

Revision ID: 5961a6ace73b
Revises: 7e03b2262e9e
Create Date: 2018-11-02 13:54:39.610928
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '5961a6ace73b'
down_revision = '7e03b2262e9e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('registrations', sa.Column('base_price_info', sa.String(), nullable=True), schema='event_registration')


def downgrade():
    op.drop_column('registrations', 'base_price_info', schema='event_registration')
