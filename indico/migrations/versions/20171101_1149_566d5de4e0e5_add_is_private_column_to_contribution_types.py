"""Add is_private column to contribution types table

Revision ID: 566d5de4e0e5
Revises: 1d512a9ebb30
Create Date: 2017-11-01 11:49:47.532339
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '566d5de4e0e5'
down_revision = '1d512a9ebb30'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'contribution_types',
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default='false'),
        schema='events'
    )
    op.alter_column('contribution_types', 'is_private', server_default=None, schema='events')


def downgrade():
    op.drop_column('contribution_types', 'is_private', schema='events')
