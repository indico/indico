"""rename IndexedEvent table to Event

Revision ID: 365fe2261342
Revises: 3778dc365e54
Create Date: 2015-08-05 15:18:10.748257
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '365fe2261342'
down_revision = '3778dc365e54'


def upgrade():
    op.rename_table('event_index', 'event', schema='events')
    op.add_column('event', sa.Column('logo', sa.LargeBinary(), nullable=True), schema='events')
    op.add_column('event', sa.Column('logo_metadata', postgresql.JSON(), nullable=True), schema='events')


def downgrade():
    op.drop_column('event', 'logo', schema='events')
    op.drop_column('event', 'logo_metadata', schema='events')
    op.rename_table('event', 'event_index', schema='events')
