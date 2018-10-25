"""Remove reservation-equipment association

Revision ID: 868c04697dd7
Revises: db32adb8fc4e
Create Date: 2018-10-25 17:10:03.543695
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '868c04697dd7'
down_revision = 'db32adb8fc4e'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('reservation_equipment', schema='roombooking')


def downgrade():
    op.create_table(
        'reservation_equipment',
        sa.Column('equipment_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('reservation_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['equipment_id'], ['roombooking.equipment_types.id']),
        sa.ForeignKeyConstraint(['reservation_id'], ['roombooking.reservations.id']),
        sa.PrimaryKeyConstraint('equipment_id', 'reservation_id'),
        schema='roombooking'
    )
