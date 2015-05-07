"""Use proper type and FK for room owner_id

Revision ID: 5a5297fea7bd
Revises: 6b0f87a586c
Create Date: 2015-05-07 18:01:29.949486
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '5a5297fea7bd'
down_revision = '6b0f87a586c'


def upgrade():
    op.execute('ALTER TABLE roombooking.rooms ALTER COLUMN owner_id TYPE int USING owner_id::int')
    op.create_foreign_key(None,
                          'rooms', 'users',
                          ['owner_id'], ['id'],
                          source_schema='roombooking', referent_schema='users')
    op.create_index(None, 'rooms', ['owner_id'], unique=False, schema='roombooking')


def downgrade():
    op.drop_index(op.f('ix_rooms_owner_id'), table_name='rooms', schema='roombooking')
    op.drop_constraint('fk_rooms_owner_id_users', 'rooms', schema='roombooking')
    op.alter_column('rooms', 'owner_id', type_=sa.String, schema='roombooking')
