"""Use json column for blocking principals

Revision ID: 51f7943e5784
Revises: 31c638d29490
Create Date: 2015-04-24 17:00:08.630888
"""

import json

import sqlalchemy as sa
from alembic import op
from alembic import context
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '51f7943e5784'
down_revision = '31c638d29490'


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    op.execute("ALTER TABLE roombooking.blocking_principals ADD COLUMN id serial NOT NULL")
    op.add_column('blocking_principals', sa.Column('principal', postgresql.JSON(), nullable=True),
                  schema='roombooking')
    res = conn.execute("SELECT id, entity_type, entity_id FROM roombooking.blocking_principals")
    for id_, entity_type, entity_id in res:
        type_ = 'User' if entity_type in {'Avatar', 'User'} else 'Group'
        principal = (type_, entity_id)
        conn.execute("UPDATE roombooking.blocking_principals SET principal=%s WHERE id=%s",
                     (json.dumps(principal), id_))
    op.alter_column('blocking_principals', 'principal', nullable=False, schema='roombooking')
    op.drop_constraint('pk_blocking_principals', 'blocking_principals', schema='roombooking')
    op.create_primary_key(None, 'blocking_principals', ['id'], schema='roombooking')
    op.drop_column('blocking_principals', 'entity_id', schema='roombooking')
    op.drop_column('blocking_principals', 'entity_type', schema='roombooking')


def downgrade():
    if context.is_offline_mode():
        raise Exception('This downgrade is only possible in online mode')
    conn = op.get_bind()
    op.add_column('blocking_principals', sa.Column('entity_type', sa.VARCHAR(), autoincrement=False, nullable=True),
                  schema='roombooking')
    op.add_column('blocking_principals', sa.Column('entity_id', sa.VARCHAR(), autoincrement=False, nullable=True),
                  schema='roombooking')
    for id_, principal in conn.execute('SELECT id, principal FROM roombooking.blocking_principals'):
        entity_type = principal[0]
        entity_id = principal[1] if not isinstance(principal[1], list) else principal[1][1]
        conn.execute("UPDATE roombooking.blocking_principals SET entity_type=%s, entity_id=%s WHERE id=%s",
                     (entity_type, entity_id, id_))
    op.alter_column('blocking_principals', 'entity_id', nullable=False, schema='roombooking')
    op.alter_column('blocking_principals', 'entity_type', nullable=False, schema='roombooking')
    op.drop_constraint('pk_blocking_principals', 'blocking_principals', schema='roombooking')
    op.create_primary_key(None, 'blocking_principals', ['blocking_id', 'entity_type', 'entity_id'],
                          schema='roombooking')
    op.drop_column('blocking_principals', 'principal', schema='roombooking')
    op.drop_column('blocking_principals', 'id', schema='roombooking')
