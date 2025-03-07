"""Add location principals table

Revision ID: b212f6d17229
Revises: 9251bc3e2106
Create Date: 2024-09-11 15:15:52.630865
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum


# revision identifiers, used by Alembic.
revision = 'b212f6d17229'
down_revision = '9251bc3e2106'
branch_labels = None
depends_on = None


class _PrincipalType(int, Enum):
    user = 1
    local_group = 2
    multipass_group = 3
    email = 4
    network = 5
    event_role = 6
    category_role = 7
    registration_form = 8


def upgrade():
    op.create_table(
        'location_principals',
        sa.Column('read_access', sa.Boolean(), nullable=False),
        sa.Column('full_access', sa.Boolean(), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False, index=True),
        sa.Column('local_group_id', sa.Integer(), nullable=True, index=True),
        sa.Column('mp_group_provider', sa.String(), nullable=True),
        sa.Column('mp_group_name', sa.String(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('type', PyIntEnum(_PrincipalType, exclude_values={_PrincipalType.email, _PrincipalType.network,
                                                                    _PrincipalType.event_role, _PrincipalType.category_role,
                                                                    _PrincipalType.registration_form}), nullable=False),
        sa.CheckConstraint('NOT read_access', name='no_read_access'),
        sa.CheckConstraint('read_access OR full_access OR array_length(permissions, 1) IS NOT NULL', name='has_privs'),
        sa.CheckConstraint('type != 1 OR (local_group_id IS NULL AND mp_group_name IS NULL AND '
                           'mp_group_provider IS NULL AND user_id IS NOT NULL)', name='valid_user'),
        sa.CheckConstraint('type != 2 OR (mp_group_name IS NULL AND mp_group_provider IS NULL AND user_id IS NULL AND '
                           'local_group_id IS NOT NULL)', name='valid_local_group'),
        sa.CheckConstraint('type != 3 OR (local_group_id IS NULL AND user_id IS NULL AND mp_group_name IS NOT NULL AND '
                           'mp_group_provider IS NOT NULL)', name='valid_multipass_group'),
        sa.ForeignKeyConstraint(['local_group_id'], ['users.groups.id']),
        sa.ForeignKeyConstraint(['location_id'], ['roombooking.locations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='roombooking'
    )
    op.create_index(None, 'location_principals', ['mp_group_provider', 'mp_group_name'], schema='roombooking')
    op.create_index('ix_uq_location_principals_user', 'location_principals', ['user_id', 'location_id'], unique=True,
                    schema='roombooking', postgresql_where=sa.text('type = 1'))
    op.create_index('ix_uq_location_principals_local_group', 'location_principals', ['local_group_id', 'location_id'], unique=True,
                    schema='roombooking', postgresql_where=sa.text('type = 2'))
    op.create_index('ix_uq_location_principals_mp_group', 'location_principals',
                    ['mp_group_provider', 'mp_group_name', 'location_id'], unique=True, schema='roombooking',
                    postgresql_where=sa.text('type = 3'))


def downgrade():
    op.drop_table('location_principals', schema='roombooking')
