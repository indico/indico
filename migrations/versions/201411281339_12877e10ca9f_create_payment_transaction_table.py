"""Create payment transaction table

Revision ID: 12877e10ca9f
Revises: 36dc8c810ca7
Create Date: 2014-11-28 13:39:53.420278
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '12877e10ca9f'
down_revision = '36dc8c810ca7'


def upgrade():
    op.create_table('payment_transactions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('registrant_id', sa.Integer(), nullable=False),
                    sa.Column('status', sa.SmallInteger(), nullable=False),
                    sa.Column('amount', sa.Numeric(precision=8, scale=2), nullable=False),
                    sa.Column('currency', sa.String(), nullable=False),
                    sa.Column('data', postgresql.JSON(), nullable=False),
                    sa.CheckConstraint('status IN (0, 1, 2, 3)'),
                    sa.CheckConstraint('amount > 0'),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('event_id', 'registrant_id'),
                    schema='events')


def downgrade():
    op.drop_table('payment_transactions', schema='events')
