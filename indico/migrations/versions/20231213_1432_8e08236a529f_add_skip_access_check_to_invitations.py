"""Add skip_access_check to invitations

Revision ID: 8e08236a529f
Revises: e2b69fe5155d
Create Date: 2023-12-13 14:32:14.666590
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '8e08236a529f'
down_revision = 'e2b69fe5155d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('invitations', sa.Column('skip_access_check', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_registration')
    op.alter_column('invitations', 'skip_access_check', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('invitations', 'skip_access_check', schema='event_registration')
