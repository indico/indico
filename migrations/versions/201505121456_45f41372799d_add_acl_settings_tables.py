"""Add acl settings tables

Revision ID: 45f41372799d
Revises: 319347ac94fe
Create Date: 2015-05-12 14:56:00.250271
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.principals import PrincipalType


# revision identifiers, used by Alembic.
revision = '45f41372799d'
down_revision = '319347ac94fe'


def upgrade():
    op.create_table(
        'settings_principals',
        sa.Column('type', PyIntEnum(PrincipalType), nullable=True),
        sa.Column('mp_group_provider', sa.String(), nullable=True),
        sa.Column('mp_group_name', sa.String(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('local_group_id', sa.Integer(), nullable=True),
        sa.CheckConstraint('module = lower(module)', name='lowercase_module'),
        sa.CheckConstraint('name = lower(name)', name='lowercase_name'),
        sa.CheckConstraint(
            'type != 1 OR (mp_group_provider IS NULL AND local_group_id IS NULL '
            'AND mp_group_name IS NULL AND user_id IS NOT NULL)',
            name='valid_user'),
        sa.CheckConstraint(
            'type != 2 OR (mp_group_provider IS NULL AND mp_group_name IS NULL '
            'AND user_id IS NULL AND local_group_id IS NOT NULL)',
            name='valid_local_group'),
        sa.CheckConstraint(
            'type != 3 OR (local_group_id IS NULL AND user_id IS NULL AND mp_group_provider IS NOT NULL AND '
            'mp_group_name IS NOT NULL)',
            name='valid_mp_group'),
        sa.ForeignKeyConstraint(['local_group_id'], ['users.groups.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_index(None, 'settings_principals', ['event_id'], schema='events')
    op.create_index(None, 'settings_principals', ['event_id', 'module'], schema='events')
    op.create_index(None, 'settings_principals', ['event_id', 'module', 'name'], schema='events')
    op.create_index(None, 'settings_principals', ['local_group_id'], schema='events')
    op.create_index(None, 'settings_principals', ['module'], schema='events')
    op.create_index(None, 'settings_principals', ['mp_group_provider', 'mp_group_name'], schema='events')
    op.create_index(None, 'settings_principals', ['name'], schema='events')
    op.create_index(None, 'settings_principals', ['user_id'], schema='events')

    op.create_table(
        'settings_principals',
        sa.Column('type', PyIntEnum(PrincipalType), nullable=True),
        sa.Column('mp_group_provider', sa.String(), nullable=True),
        sa.Column('mp_group_name', sa.String(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('local_group_id', sa.Integer(), nullable=True),
        sa.CheckConstraint('module = lower(module)', name='lowercase_module'),
        sa.CheckConstraint('name = lower(name)', name='lowercase_name'),
        sa.CheckConstraint(
            'type != 1 OR (mp_group_provider IS NULL AND local_group_id IS NULL AND '
            'mp_group_name IS NULL AND user_id IS NOT NULL)',
            name='valid_user'
        ),
        sa.CheckConstraint(
            'type != 2 OR (mp_group_provider IS NULL AND mp_group_name IS NULL AND '
            'user_id IS NULL AND local_group_id IS NOT NULL)',
            name='valid_local_group'
        ),
        sa.CheckConstraint(
            'type != 3 OR (local_group_id IS NULL AND user_id IS NULL AND mp_group_provider IS NOT NULL AND '
            'mp_group_name IS NOT NULL)',
            name='valid_mp_group'
        ),
        sa.ForeignKeyConstraint(['local_group_id'], ['users.groups.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='indico'
    )
    op.create_index(None, 'settings_principals', ['module'], schema='indico')
    op.create_index(None, 'settings_principals', ['name'], schema='indico')
    op.create_index(None, 'settings_principals', ['module', 'name'], schema='indico')
    op.create_index(None, 'settings_principals', ['user_id'], schema='indico')
    op.create_index(None, 'settings_principals', ['local_group_id'], schema='indico')
    op.create_index(None, 'settings_principals', ['mp_group_provider', 'mp_group_name'], schema='indico')


def downgrade():
    op.drop_table('settings_principals', schema='indico')
    op.drop_table('settings_principals', schema='events')
