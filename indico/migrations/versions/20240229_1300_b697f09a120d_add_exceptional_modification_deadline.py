"""Add exceptional modification deadline to registrations

Revision ID: b697f09a120d
Revises: 492c6d801a4a
Create Date: 2024-01-29 16:35:54.553459
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime


# revision identifiers, used by Alembic.
revision = 'b697f09a120d'
down_revision = '492c6d801a4a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('registrations',
                  sa.Column('modification_end_dt', UTCDateTime, nullable=True),
                  schema='event_registration')


def downgrade():
    op.drop_column('registrations', 'modification_end_dt', schema='event_registration')
