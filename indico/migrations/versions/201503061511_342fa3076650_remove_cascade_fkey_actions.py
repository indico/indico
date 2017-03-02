"""Remove cascade fkey actions

Revision ID: 342fa3076650
Revises: 49ac5164a65b
Create Date: 2015-03-06 15:11:53.946358
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '342fa3076650'
down_revision = '49ac5164a65b'


def upgrade():
    fkey_kwargs = {'source_schema': 'roombooking', 'referent_schema': 'roombooking'}
    op.drop_constraint('room_equipment_equipment_id_fkey', 'room_equipment', schema='roombooking')
    op.create_foreign_key('room_equipment_equipment_id_fkey',
                          'room_equipment', 'equipment_types',
                          ['equipment_id'], ['id'],
                          **fkey_kwargs)
    op.drop_constraint('room_equipment_room_id_fkey', 'room_equipment', schema='roombooking')
    op.create_foreign_key('room_equipment_room_id_fkey',
                          'room_equipment', 'rooms',
                          ['room_id'], ['id'],
                          **fkey_kwargs)
    op.drop_constraint('reservation_equipment_equipment_id_fkey', 'reservation_equipment', schema='roombooking')
    op.create_foreign_key('reservation_equipment_equipment_id_fkey',
                          'reservation_equipment', 'equipment_types',
                          ['equipment_id'], ['id'],
                          **fkey_kwargs)
    op.drop_constraint('reservation_equipment_reservation_id_fkey', 'reservation_equipment', schema='roombooking')
    op.create_foreign_key('reservation_equipment_reservation_id_fkey',
                          'reservation_equipment', 'reservations',
                          ['reservation_id'], ['id'],
                          **fkey_kwargs)


def downgrade():
    fkey_kwargs = {'source_schema': 'roombooking', 'referent_schema': 'roombooking', 'ondelete': 'CASCADE'}
    op.drop_constraint('room_equipment_equipment_id_fkey', 'room_equipment', schema='roombooking')
    op.create_foreign_key('room_equipment_equipment_id_fkey',
                          'room_equipment', 'equipment_types',
                          ['equipment_id'], ['id'],
                          **fkey_kwargs)
    op.drop_constraint('room_equipment_room_id_fkey', 'room_equipment', schema='roombooking')
    op.create_foreign_key('room_equipment_room_id_fkey',
                          'room_equipment', 'rooms',
                          ['room_id'], ['id'],
                          **fkey_kwargs)
    op.drop_constraint('reservation_equipment_equipment_id_fkey', 'reservation_equipment', schema='roombooking')
    op.create_foreign_key('reservation_equipment_equipment_id_fkey',
                          'reservation_equipment', 'equipment_types',
                          ['equipment_id'], ['id'],
                          **fkey_kwargs)
    op.drop_constraint('reservation_equipment_reservation_id_fkey', 'reservation_equipment', schema='roombooking')
    op.create_foreign_key('reservation_equipment_reservation_id_fkey',
                          'reservation_equipment', 'reservations',
                          ['reservation_id'], ['id'],
                          **fkey_kwargs)
