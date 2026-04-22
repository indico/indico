"""Add modified_dt column to registrations

Revision ID: add_registration_modified_dt
Revises: 577e564cf0ae
Create Date: 2026-04-22 12:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = 'add_registration_modified_dt'
down_revision = '577e564cf0ae'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('registrations', sa.Column('modified_dt', UTCDateTime(), nullable=True),
                  schema='event_registration')


def downgrade():
    op.drop_column('registrations', 'modified_dt', schema='event_registration')
