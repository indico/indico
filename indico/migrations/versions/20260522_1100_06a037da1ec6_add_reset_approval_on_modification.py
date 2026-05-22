"""Add reset_approval_on_modification column to registration forms

Revision ID: 06a037da1ec6
Revises: e1e229910f7e
Create Date: 2026-05-22 11:00:00.000000
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '06a037da1ec6'
down_revision = 'e1e229910f7e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'forms',
        sa.Column('reset_approval_on_modification', sa.Boolean(), nullable=False, server_default='false'),
        schema='event_registration',
    )
    op.alter_column('forms', 'reset_approval_on_modification', server_default=None,
                    schema='event_registration')


def downgrade():
    op.drop_column('forms', 'reset_approval_on_modification', schema='event_registration')
