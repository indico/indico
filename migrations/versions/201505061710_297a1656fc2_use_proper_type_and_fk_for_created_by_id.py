"""Use proper type and FK for created_by_id

Revision ID: 297a1656fc2
Revises: 3b997c7a4f0c
Create Date: 2015-05-06 17:10:01.011120
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '297a1656fc2'
down_revision = '3b997c7a4f0c'


def upgrade():
    op.execute('ALTER TABLE roombooking.reservations ALTER COLUMN created_by_id TYPE int USING created_by_id::int')
    op.create_foreign_key(None,
                          'reservations', 'users',
                          ['created_by_id'], ['id'],
                          source_schema='roombooking', referent_schema='users')
    op.create_index(None, 'reservations', ['created_by_id'], unique=False, schema='roombooking')


def downgrade():
    op.drop_index(op.f('ix_reservations_created_by_id'), table_name='reservations', schema='roombooking')
    op.drop_constraint('fk_reservations_created_by_id_users', 'reservations', schema='roombooking')
    op.alter_column('reservations', 'created_by_id', type_=sa.String, schema='roombooking')
