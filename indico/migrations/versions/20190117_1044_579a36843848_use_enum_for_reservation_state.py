"""Use enum for reservation state

Revision ID: 579a36843848
Revises: cbe630695800
Create Date: 2019-01-17 10:44:56.778419
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.rb.models.reservations import ReservationState


# revision identifiers, used by Alembic.
revision = '579a36843848'
down_revision = 'cbe630695800'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reservations', sa.Column('state', PyIntEnum(ReservationState), nullable=True), schema='roombooking')
    op.execute('''
        UPDATE roombooking.reservations
        SET state = CASE
            WHEN is_rejected THEN 4
            WHEN is_cancelled THEN 3
            WHEN is_accepted THEN 2
            ELSE 1
        END
    ''')
    op.alter_column('reservations', 'state', nullable=False, schema='roombooking')
    op.drop_column('reservations', 'is_accepted', schema='roombooking')
    op.drop_column('reservations', 'is_cancelled', schema='roombooking')
    op.drop_column('reservations', 'is_rejected', schema='roombooking')


def downgrade():
    op.add_column('reservations', sa.Column('is_rejected', sa.Boolean(), nullable=True), schema='roombooking')
    op.add_column('reservations', sa.Column('is_accepted', sa.Boolean(), nullable=True), schema='roombooking')
    op.add_column('reservations', sa.Column('is_cancelled', sa.Boolean(), nullable=True), schema='roombooking')
    op.execute('''
        UPDATE roombooking.reservations
        SET is_accepted = (state = 2),
            is_cancelled = (state = 3),
            is_rejected = (state = 4)
    ''')
    op.alter_column('reservations', 'is_accepted', nullable=False, schema='roombooking')
    op.alter_column('reservations', 'is_rejected', nullable=False, schema='roombooking')
    op.alter_column('reservations', 'is_cancelled', nullable=False, schema='roombooking')
    op.drop_column('reservations', 'state', schema='roombooking')
