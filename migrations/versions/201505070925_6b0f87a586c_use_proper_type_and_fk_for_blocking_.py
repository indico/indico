"""Use proper type and FK for blocking created_by_id

Revision ID: 6b0f87a586c
Revises: 297a1656fc2
Create Date: 2015-05-07 09:25:17.068950
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '6b0f87a586c'
down_revision = '297a1656fc2'


def upgrade():
    op.execute('ALTER TABLE roombooking.blockings ALTER COLUMN created_by_id TYPE int USING created_by_id::int')
    op.create_foreign_key(None,
                          'blockings', 'users',
                          ['created_by_id'], ['id'],
                          source_schema='roombooking', referent_schema='users')
    op.create_index(None, 'blockings', ['created_by_id'], unique=False, schema='roombooking')


def downgrade():
    op.drop_index(op.f('ix_blockings_created_by_id'), table_name='blockings', schema='roombooking')
    op.drop_constraint('fk_blockings_created_by_id_users', 'blockings', schema='roombooking')
    op.alter_column('blockings', 'created_by_id', type_=sa.String, schema='roombooking')
