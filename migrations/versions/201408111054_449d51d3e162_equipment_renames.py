"""Equipment renames

Revision ID: 449d51d3e162
Revises: 23d5b16a389e
Create Date: 2014-08-11 10:54:13.798760
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '449d51d3e162'
down_revision = '23d5b16a389e'


def upgrade():
    op.rename_table('room_equipments', 'equipment_types')
    op.rename_table('rooms_equipments', 'room_equipment')
    op.rename_table('reservations_equipments', 'reservation_equipment')


def downgrade():
    op.rename_table('reservation_equipment', 'reservations_equipments')
    op.rename_table('room_equipment', 'rooms_equipments')
    op.rename_table('equipment_types', 'room_equipments')
