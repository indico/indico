"""Add partial_completion to survey

Revision ID: eb58b6e68c19
Revises: fa640196be8
Create Date: 2017-03-20 11:05:19.349023
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'eb58b6e68c19'
down_revision = 'fa640196be8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('surveys',
                  sa.Column('partial_completion', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_surveys')
    op.alter_column('surveys', 'partial_completion', server_default=None, schema='event_surveys')


def downgrade():
    op.drop_column('surveys', 'partial_completion', schema='event_surveys')
