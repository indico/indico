"""Add event acls

Revision ID: 47977407fa2b
Revises: 3b6c768b8803
Create Date: 2015-09-07 16:38:32.486270
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.protection import ProtectionMode

from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '47977407fa2b'
down_revision = '3b6c768b8803'


def upgrade():
    op.create_table(
        'principals',
        sa.Column('mp_group_provider', sa.String(), nullable=True),
        sa.Column('mp_group_name', sa.String(), nullable=True),
        sa.Column('read_access', sa.Boolean(), nullable=False),
        sa.Column('full_access', sa.Boolean(), nullable=False),
        sa.Column('roles', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('local_group_id', sa.Integer(), nullable=True, index=True),
        sa.Column('type', PyIntEnum(PrincipalType), nullable=True),
        sa.Column('email', sa.String(), nullable=True, index=True),
        sa.Index('ix_uq_principals_user', 'user_id', 'event_id', unique=True, postgresql_where=sa.text('type = 1')),
        sa.Index('ix_uq_principals_local_group', 'local_group_id', 'event_id', unique=True,
                 postgresql_where=sa.text('type = 2')),
        sa.Index('ix_uq_principals_mp_group', 'mp_group_provider', 'mp_group_name', 'event_id', unique=True,
                 postgresql_where=sa.text('type = 3')),
        sa.Index('ix_uq_principals_email', 'email', 'event_id', unique=True, postgresql_where=sa.text('type = 4')),
        sa.CheckConstraint('type != 1 OR (local_group_id IS NULL AND mp_group_provider IS NULL AND email IS NULL AND '
                           'mp_group_name IS NULL AND user_id IS NOT NULL)',
                           name='valid_user'),
        sa.CheckConstraint('type != 2 OR (user_id IS NULL AND mp_group_provider IS NULL AND email IS NULL AND '
                           'mp_group_name IS NULL AND local_group_id IS NOT NULL)',
                           name='valid_local_group'),
        sa.CheckConstraint('type != 3 OR (local_group_id IS NULL AND user_id IS NULL AND email IS NULL AND '
                           'mp_group_provider IS NOT NULL AND mp_group_name IS NOT NULL)',
                           name='valid_multipass_group'),
        sa.CheckConstraint('type != 4 OR (local_group_id IS NULL AND mp_group_provider IS NULL AND '
                           'mp_group_name IS NULL AND user_id IS NULL AND email IS NOT NULL)',
                           name='valid_email'),
        sa.CheckConstraint('email IS NULL OR email = lower(email)', name='lowercase_email'),
        sa.CheckConstraint('read_access OR full_access OR array_length(roles, 1) IS NOT NULL', name='has_privs'),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['local_group_id'], ['users.groups.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_index(None, 'principals', ['mp_group_provider', 'mp_group_name'], schema='events')
    op.add_column('events', sa.Column('protection_mode', PyIntEnum(ProtectionMode), nullable=False,
                                      server_default=str(ProtectionMode.inheriting.value)), schema='events')
    op.alter_column('events', 'protection_mode', server_default=None, schema='events')


def downgrade():
    op.drop_column('events', 'protection_mode', schema='events')
    op.drop_table('principals', schema='events')
