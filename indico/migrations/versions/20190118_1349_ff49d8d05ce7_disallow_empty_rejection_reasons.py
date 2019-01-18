"""Disallow empty rejection reasons

Revision ID: ff49d8d05ce7
Revises: 7ec3949a21c7
Create Date: 2019-01-18 13:49:51.797079
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'ff49d8d05ce7'
down_revision = '7ec3949a21c7'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE roombooking.reservations SET rejection_reason = NULL WHERE rejection_reason = ''")
    op.execute("UPDATE roombooking.reservation_occurrences SET rejection_reason = NULL WHERE rejection_reason = ''")
    op.create_check_constraint('rejection_reason_not_empty', 'reservations', "rejection_reason != ''",
                               schema='roombooking')
    op.create_check_constraint('rejection_reason_not_empty', 'reservation_occurrences', "rejection_reason != ''",
                               schema='roombooking')


def downgrade():
    op.drop_constraint('ck_reservations_rejection_reason_not_empty', 'reservations', schema='roombooking')
    op.drop_constraint('ck_reservation_occurrences_rejection_reason_not_empty', 'reservation_occurrences',
                       schema='roombooking')
