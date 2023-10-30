"""Add modified date to editing revisions

Revision ID: 31b699664893
Revises: 155cfc134f0c
Create Date: 2023-10-30 14:34:52.696469
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime


# revision identifiers, used by Alembic.
revision = '31b699664893'
down_revision = '155cfc134f0c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('revisions', sa.Column('modified_dt', UTCDateTime, nullable=True), schema='event_editing')


def downgrade():
    op.drop_column('revisions', 'modified_dt', schema='event_editing')
