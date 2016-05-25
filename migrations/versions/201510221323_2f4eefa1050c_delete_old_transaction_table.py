"""Delete old transaction table

Revision ID: 2f4eefa1050c
Revises: 38641fb3afac
Create Date: 2015-10-22 13:23:42.602410
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy import UTCDateTime
from indico.modules.events.payment.models.transactions import TransactionStatus


# revision identifiers, used by Alembic.
revision = '2f4eefa1050c'
down_revision = '38641fb3afac'


def upgrade():
    op.drop_table('payment_transactions_old', schema='events')


def downgrade():
    op.create_table(
        'payment_transactions_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('registrant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('status', PyIntEnum(TransactionStatus), nullable=False),
        sa.Column('amount', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('timestamp', UTCDateTime, nullable=False),
        sa.Column('data', postgresql.JSON(), nullable=False),
        sa.CheckConstraint('amount > 0', name='positive_amount'),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
