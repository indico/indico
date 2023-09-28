"""Add created_dt on User model

Revision ID: d8562ad31e90
Revises: 0c44046dc1be
Create Date: 2023-09-28 17:03:58.549354
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = 'd8562ad31e90'
down_revision = '0c44046dc1be'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('created_dt', UTCDateTime, nullable=True), schema='users')


def downgrade():
    op.drop_column('users', 'created_dt', schema='users')
