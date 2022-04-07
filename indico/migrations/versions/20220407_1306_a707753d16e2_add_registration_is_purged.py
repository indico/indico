"""Add 'is_purged' flag to registration forms

Revision ID: a707753d16e2
Revises: 88eb87ee0d3e
Create Date: 2022-04-07 13:06:45.650413
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a707753d16e2'
down_revision = '88eb87ee0d3e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('forms',
                  sa.Column('is_purged', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_registration')
    op.alter_column('forms', 'is_purged', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('forms', 'is_purged', schema='event_registration')
