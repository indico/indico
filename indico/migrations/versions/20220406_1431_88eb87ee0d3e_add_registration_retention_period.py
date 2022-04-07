"""Add retention period to RegistrationForm

Revision ID: 88eb87ee0d3e
Revises: a61ce4bd7549
Create Date: 2022-04-06 14:31:21.967431
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '88eb87ee0d3e'
down_revision = 'a61ce4bd7549'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms', sa.Column('retention_period', sa.Interval(), nullable=True), schema='event_registration')


def downgrade():
    op.drop_column('forms', 'retention_period', schema='event_registration')
