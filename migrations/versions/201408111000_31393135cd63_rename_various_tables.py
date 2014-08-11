"""Rename various tables

Revision ID: 31393135cd63
Revises: 15d40b3663b9
Create Date: 2014-08-11 10:00:39.708277
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '31393135cd63'
down_revision = '15d40b3663b9'


def upgrade():
    op.rename_table('room_bookable_times', 'room_bookable_hours')
    op.rename_table('room_nonbookable_dates', 'room_nonbookable_periods')


def downgrade():
    op.rename_table('room_nonbookable_periods', 'room_nonbookable_dates')
    op.rename_table('room_bookable_hours', 'room_bookable_times')
