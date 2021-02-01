"""add 'rejection_reason' to registration.

Revision ID: e787389ca868
Revises: e4fb983dc64c
Create Date: 2021-01-29 22:32:11.206740
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'e787389ca868'
down_revision = 'e4fb983dc64c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('registrations', sa.Column('rejection_reason', sa.String(), server_default='', nullable=False),
                  schema='event_registration')


def downgrade():
    op.drop_column('registrations', 'rejection_reason', schema='event_registration')
