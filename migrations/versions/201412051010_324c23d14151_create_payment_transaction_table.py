"""Create payment transaction table

Revision ID: 324c23d14151
Revises: 36dc8c810ca7
Create Date: 2014-12-05 10:10:04.325749
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime

# revision identifiers, used by Alembic.
revision = '324c23d14151'
down_revision = '36dc8c810ca7'


def upgrade():
    op.create_table('payment_transactions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('registrant_id', sa.Integer(), nullable=False),
                    sa.Column('status', sa.SmallInteger(), nullable=False),
                    sa.Column('amount', sa.Numeric(precision=8, scale=2), nullable=False),
                    sa.Column('currency', sa.String(), nullable=False),
                    sa.Column('timestamp', UTCDateTime(), nullable=False, index=True),
                    sa.Column('provider', sa.String(), nullable=False),
                    sa.Column('data', postgresql.JSON(), nullable=False),
                    sa.CheckConstraint('amount > 0', 'positive_amount'),
                    sa.CheckConstraint('status IN (1, 2, 3, 4, 5)', 'valid_enum_status'),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('event_id', 'registrant_id', 'timestamp'),
                    schema='events')


def downgrade():
    op.drop_table('payment_transactions', schema='events')
