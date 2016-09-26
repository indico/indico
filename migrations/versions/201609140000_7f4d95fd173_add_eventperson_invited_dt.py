"""Add EventPerson invited_dt

Revision ID: 7f4d95fd173
Revises: 2ce1756a2f12
Create Date: 2016-09-23 15:39:19.832557
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '7f4d95fd173'
down_revision = '2ce1756a2f12'


def upgrade():
    op.add_column('persons', sa.Column('invited_dt', UTCDateTime, nullable=True), schema='events')


def downgrade():
    op.drop_column('persons', 'invited_dt', schema='events')
