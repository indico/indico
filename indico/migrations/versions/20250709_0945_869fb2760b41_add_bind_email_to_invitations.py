"""Add bind_email to invitations

Revision ID: 869fb2760b41
Revises: a5b6d7237997
Create Date: 2025-07-09 09:45:37.624332
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '869fb2760b41'
down_revision = 'a5b6d7237997'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('invitations', sa.Column('bind_email', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_registration')
    op.alter_column('invitations', 'bind_email', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('invitations', 'bind_email', schema='event_registration')
