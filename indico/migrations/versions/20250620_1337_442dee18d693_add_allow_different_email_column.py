"""Add allow_different_email column

Revision ID: 442dee18d693
Revises: a5b6d7237997
Create Date: 2025-06-17 19:29:43.620509
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '442dee18d693'
down_revision = 'a5b6d7237997'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('invitations', sa.Column('allow_different_email', sa.Boolean(), nullable=False,
                                           server_default='false'), schema='event_registration')
    op.alter_column('invitations', 'allow_different_email', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('invitations', 'allow_different_email', schema='event_registration')
