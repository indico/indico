"""Use proper type and FK for booked_for_id

Revision ID: 3b997c7a4f0c
Revises: 2bb9dc6f5c28
Create Date: 2015-05-06 14:04:14.590496
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '3b997c7a4f0c'
down_revision = '2bb9dc6f5c28'


def upgrade():
    op.execute('ALTER TABLE roombooking.reservations ALTER COLUMN booked_for_id TYPE int USING booked_for_id::int')
    op.create_foreign_key(None,
                          'reservations', 'users',
                          ['booked_for_id'], ['id'],
                          source_schema='roombooking', referent_schema='users')
    op.create_index(None, 'reservations', ['booked_for_id'], unique=False, schema='roombooking')


def downgrade():
    op.drop_index(op.f('ix_reservations_booked_for_id'), table_name='reservations', schema='roombooking')
    op.drop_constraint('fk_reservations_booked_for_id_users', 'reservations', schema='roombooking')
    op.alter_column('reservations', 'booked_for_id', type_=sa.String, schema='roombooking')
