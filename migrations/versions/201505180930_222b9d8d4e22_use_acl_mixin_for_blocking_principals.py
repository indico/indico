"""Use ACL mixin for blocking principals

Revision ID: 222b9d8d4e22
Revises: 45f41372799d
Create Date: 2015-05-18 09:30:24.938982
"""

import json

import sqlalchemy as sa
from alembic import op, context
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.util.convert_acl_settings import _principal_to_args, _args_to_principal


# revision identifiers, used by Alembic.
revision = '222b9d8d4e22'
down_revision = '45f41372799d'


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    op.add_column('blocking_principals', sa.Column('local_group_id', sa.Integer(), nullable=True),
                  schema='roombooking')
    op.add_column('blocking_principals', sa.Column('mp_group_name', sa.String(), nullable=True),
                  schema='roombooking')
    op.add_column('blocking_principals', sa.Column('mp_group_provider', sa.String(), nullable=True),
                  schema='roombooking')
    op.add_column('blocking_principals', sa.Column('type', PyIntEnum(PrincipalType), nullable=True),
                  schema='roombooking')
    op.add_column('blocking_principals', sa.Column('user_id', sa.Integer(), nullable=True), schema='roombooking')
    res = conn.execute("SELECT id, principal FROM roombooking.blocking_principals")
    for id_, principal in res:
        args = _principal_to_args(principal)
        conn.execute("UPDATE roombooking.blocking_principals SET type = %s, user_id = %s, local_group_id = %s, "
                     "mp_group_provider = %s, mp_group_name = %s WHERE id = %s", args + (id_,))
    op.drop_column('blocking_principals', 'principal', schema='roombooking')
    op.create_index(None, 'blocking_principals', ['local_group_id'], schema='roombooking')
    op.create_index(None, 'blocking_principals', ['user_id'], schema='roombooking')
    op.create_foreign_key(None,
                          'blocking_principals', 'users',
                          ['user_id'], ['id'],
                          source_schema='roombooking', referent_schema='users')
    op.create_foreign_key(None,
                          'blocking_principals', 'groups',
                          ['local_group_id'], ['id'],
                          source_schema='roombooking', referent_schema='users')


def downgrade():
    if context.is_offline_mode():
        raise Exception('This downgrade is only possible in online mode')
    conn = op.get_bind()
    op.add_column('blocking_principals', sa.Column('principal', postgresql.JSON(), autoincrement=False, nullable=True),
                  schema='roombooking')
    res = conn.execute("SELECT id, type, user_id, local_group_id, mp_group_provider, mp_group_name FROM "
                       "roombooking.blocking_principals")
    for row in res:
        id_ = row[0]
        principal = _args_to_principal(*row[1:])
        conn.execute("UPDATE roombooking.blocking_principals SET principal = %s WHERE id = %s",
                     (json.dumps(principal), id_))
    op.alter_column('blocking_principals', 'principal', nullable=False, schema='roombooking')
    op.drop_column('blocking_principals', 'user_id', schema='roombooking')
    op.drop_column('blocking_principals', 'type', schema='roombooking')
    op.drop_column('blocking_principals', 'mp_group_provider', schema='roombooking')
    op.drop_column('blocking_principals', 'mp_group_name', schema='roombooking')
    op.drop_column('blocking_principals', 'local_group_id', schema='roombooking')
