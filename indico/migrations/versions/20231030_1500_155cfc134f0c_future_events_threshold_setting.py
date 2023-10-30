"""Setting for future events threshold

Revision ID: 155cfc134f0c
Revises: 13d8ba15a83b
Create Date: 2023-09-13 21:16:13.839731
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '155cfc134f0c'
down_revision = '13d8ba15a83b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('categories', sa.Column('show_future_months', sa.Integer(), nullable=False, server_default='0'),
                  schema='categories')
    op.alter_column('categories', 'show_future_months', server_default=None, schema='categories')


def downgrade():
    op.drop_column('categories', 'show_future_months', schema='categories')
