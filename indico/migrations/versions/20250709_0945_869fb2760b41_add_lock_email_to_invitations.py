"""Add lock_email to invitations

Revision ID: 869fb2760b41
Revises: b4ee48f3052c
Create Date: 2025-07-09 09:45:37.624332
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '869fb2760b41'
down_revision = 'b4ee48f3052c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('invitations', sa.Column('lock_email', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_registration')
    op.alter_column('invitations', 'lock_email', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('invitations', 'lock_email', schema='event_registration')
