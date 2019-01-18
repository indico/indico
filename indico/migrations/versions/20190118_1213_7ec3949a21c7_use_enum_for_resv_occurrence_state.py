"""Use enum for resv occurrence state

Revision ID: 7ec3949a21c7
Revises: 579a36843848
Create Date: 2019-01-18 12:13:42.042274
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrenceState


# revision identifiers, used by Alembic.
revision = '7ec3949a21c7'
down_revision = '579a36843848'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reservation_occurrences', sa.Column('state', PyIntEnum(ReservationOccurrenceState), nullable=True),
                  schema='roombooking')
    op.execute('''
        UPDATE roombooking.reservation_occurrences
        SET state = CASE
            WHEN is_rejected THEN 4
            WHEN is_cancelled THEN 3
            ELSE 2
        END
    ''')
    op.alter_column('reservation_occurrences', 'state', nullable=False, schema='roombooking')
    op.drop_column('reservation_occurrences', 'is_cancelled', schema='roombooking')
    op.drop_column('reservation_occurrences', 'is_rejected', schema='roombooking')


def downgrade():
    op.add_column('reservation_occurrences', sa.Column('is_rejected', sa.Boolean(), nullable=True),
                  schema='roombooking')
    op.add_column('reservation_occurrences', sa.Column('is_cancelled', sa.Boolean(), nullable=True),
                  schema='roombooking')
    op.execute('''
       UPDATE roombooking.reservation_occurrences
       SET is_cancelled = (state = 3),
           is_rejected = (state = 4)
    ''')
    op.alter_column('reservation_occurrences', 'is_rejected', nullable=False, schema='roombooking')
    op.alter_column('reservation_occurrences', 'is_cancelled', nullable=False, schema='roombooking')
    op.drop_column('reservation_occurrences', 'state', schema='roombooking')
