"""Force accepting terms of service

Revision ID: e4ac92d27295
Revises: 17996ef18cb9
Create Date: 2023-12-11 23:20:56.153443
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = 'e4ac92d27295'
down_revision = '17996ef18cb9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('accepted_tos_dt', UTCDateTime, nullable=True), schema='users')


def downgrade():
    op.drop_column('users', 'accepted_tos_dt', schema='users')
