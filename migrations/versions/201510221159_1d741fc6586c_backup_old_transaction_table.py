"""Backup old transaction table

Revision ID: 1d741fc6586c
Revises: f9bb2a03ceb
Create Date: 2015-10-22 11:59:18.116917
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.db.sqlalchemy.util.bulk_rename import _rename_constraint
from indico.modules.events.payment.models.transactions import TransactionStatus


# revision identifiers, used by Alembic.
revision = '1d741fc6586c'
down_revision = 'f9bb2a03ceb'


def upgrade():
    op.rename_table('payment_transactions', 'payment_transactions_old', schema='events')
    op.execute(_rename_constraint('events', 'payment_transactions_old',
                                  'pk_payment_transactions', 'pk_payment_transactions_old'))
    op.execute("ALTER SEQUENCE events.payment_transactions_id_seq RENAME TO payment_transactions_old_id_seq")
    op.create_table(
        'payment_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('registration_id', sa.Integer(), nullable=False, index=True),
        sa.Column('status', PyIntEnum(TransactionStatus), nullable=False),
        sa.Column('amount', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('timestamp', UTCDateTime, nullable=False),
        sa.Column('data', postgresql.JSON(), nullable=False),
        sa.CheckConstraint('amount > 0', name='positive_amount'),
        sa.ForeignKeyConstraint(['registration_id'], ['event_registration.registrations.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_foreign_key(None,
                          'registrations', 'payment_transactions',
                          ['transaction_id'], ['id'],
                          source_schema='event_registration', referent_schema='events')


def downgrade():
    op.drop_constraint(op.f('fk_registrations_transaction_id_payment_transactions'), 'registrations',
                       schema='event_registration')
    op.drop_table('payment_transactions', schema='events')
    op.execute("ALTER SEQUENCE events.payment_transactions_old_id_seq RENAME TO payment_transactions_id_seq")
    op.execute(_rename_constraint('events', 'payment_transactions_old',
                                  'pk_payment_transactions_old', 'pk_payment_transactions'))
    op.rename_table('payment_transactions_old', 'payment_transactions', schema='events')
