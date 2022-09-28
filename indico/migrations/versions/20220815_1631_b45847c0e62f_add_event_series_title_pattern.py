"""Add event series title pattern

Revision ID: b45847c0e62f
Revises: b60f5c45acf7
Create Date: 2022-08-15 16:31:56.529409
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b45847c0e62f'
down_revision = 'b60f5c45acf7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('series', sa.Column('event_title_pattern', sa.String(), server_default='', nullable=False),
                  schema='events')
    op.alter_column('series', 'event_title_pattern', server_default=None, schema='events')


def downgrade():
    op.drop_column('series', 'event_title_pattern', schema='events')
