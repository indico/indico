"""Add regform withdraw_outside_modification

Revision ID: 91cd48f93283
Revises: 06a037da1ec6
Create Date: 2026-10-01 10:06:43.664117
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '91cd48f93283'
down_revision = '06a037da1ec6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'forms',
        sa.Column('withdraw_outside_modification', sa.Boolean(), nullable=False, server_default='false'),
        schema='event_registration',
    )
    op.alter_column('forms', 'withdraw_outside_modification', server_default=None, schema='event_registration')


def downgrade():
    op.drop_column('forms', 'withdraw_outside_modification', schema='event_registration')
