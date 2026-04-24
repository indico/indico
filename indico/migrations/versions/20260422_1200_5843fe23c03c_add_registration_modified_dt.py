"""Add modified_dt column to registrations

Revision ID: 5843fe23c03c
Revises: e5a08c20f2bc
Create Date: 2026-04-22 12:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '5843fe23c03c'
down_revision = 'e5a08c20f2bc'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('registrations', sa.Column('modified_dt', UTCDateTime(), nullable=True), schema='event_registration')


def downgrade():
    op.drop_column('registrations', 'modified_dt', schema='event_registration')
