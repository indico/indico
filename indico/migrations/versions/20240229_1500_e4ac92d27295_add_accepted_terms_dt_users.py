"""Add accepted_terms_dt to users

Revision ID: e4ac92d27295
Revises: b697f09a120d
Create Date: 2023-12-11 23:20:56.153443
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = 'e4ac92d27295'
down_revision = 'b697f09a120d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('accepted_terms_dt', UTCDateTime, nullable=True), schema='users')


def downgrade():
    op.drop_column('users', 'accepted_terms_dt', schema='users')
