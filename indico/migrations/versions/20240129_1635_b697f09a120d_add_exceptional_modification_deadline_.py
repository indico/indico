"""Add exceptional modification deadline to registrations

Revision ID: b697f09a120d
Revises: 8e08236a529f
Create Date: 2024-01-29 16:35:54.553459
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime


# revision identifiers, used by Alembic.
revision = 'b697f09a120d'
down_revision = '8e08236a529f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('registrations',
                  sa.Column('exceptional_modification_allowed_end_dt', UTCDateTime, nullable=True), schema='event_registration')


def downgrade():
    op.drop_column('registrations', 'exceptional_modification_allowed_end_dt', schema='event_registration')
