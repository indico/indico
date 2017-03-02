"""Add category tables

Revision ID: 3032079d8b33
Revises: abf75c26dc4
Create Date: 2016-06-01 14:13:14.622045
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.categories.models.categories import EventMessageMode


# revision identifiers, used by Alembic.
revision = '3032079d8b33'
down_revision = 'abf75c26dc4'


def upgrade():
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True, index=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('visibility', sa.Integer(), nullable=True),
        sa.Column('icon_metadata', pg.JSON(), nullable=False),
        sa.Column('icon', sa.LargeBinary(), nullable=True),
        sa.Column('logo_metadata', pg.JSON(), nullable=False),
        sa.Column('logo', sa.LargeBinary(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=False),
        sa.Column('default_event_themes', pg.JSON(), nullable=False),
        sa.Column('event_creation_restricted', sa.Boolean(), nullable=False),
        sa.Column('event_creation_notification_emails', pg.ARRAY(sa.String()), nullable=False),
        sa.Column('notify_managers', sa.Boolean(), nullable=False),
        sa.Column('event_message_mode', PyIntEnum(EventMessageMode), nullable=False),
        sa.Column('event_message', sa.Text(), nullable=False),
        sa.Column('no_access_contact', sa.String(), nullable=False),
        sa.Column('suggestions_disabled', sa.Boolean(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('protection_mode', PyIntEnum(ProtectionMode), nullable=False),
        sa.CheckConstraint("(icon IS NULL) = (icon_metadata::text = 'null')", name='valid_icon'),
        sa.CheckConstraint("(logo IS NULL) = (logo_metadata::text = 'null')", name='valid_logo'),
        sa.CheckConstraint("title != ''", name='valid_title'),
        sa.CheckConstraint('(id != 0) OR NOT is_deleted', name='root_not_deleted'),
        sa.CheckConstraint('(id != 0) OR (protection_mode != 1)', name='root_not_inheriting'),
        sa.CheckConstraint('(parent_id IS NULL) = (id = 0)', name='valid_parent'),
        sa.CheckConstraint('visibility IS NULL OR visibility > 0', name='valid_visibility'),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.categories.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='categories'
    )
    op.create_index(op.f('ix_categories_title_fts'), 'categories', [sa.text("to_tsvector('simple', title)")],
                    schema='categories', postgresql_using='gin')
    op.create_table(
        'principals',
        sa.Column('read_access', sa.Boolean(), nullable=False),
        sa.Column('full_access', sa.Boolean(), nullable=False),
        sa.Column('roles', pg.ARRAY(sa.String()), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('mp_group_provider', sa.String(), nullable=True),
        sa.Column('mp_group_name', sa.String(), nullable=True),
        sa.Column('local_group_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('ip_network_group_id', sa.Integer(), nullable=True),
        sa.Column('type', PyIntEnum(PrincipalType, exclude_values={PrincipalType.email}), nullable=False),
        sa.CheckConstraint('read_access OR full_access OR array_length(roles, 1) IS NOT NULL', name='has_privs'),
        sa.CheckConstraint('type != 1 OR (ip_network_group_id IS NULL AND local_group_id IS NULL AND '
                           'mp_group_name IS NULL AND mp_group_provider IS NULL AND user_id IS NOT NULL)',
                           name='valid_user'),
        sa.CheckConstraint('type != 2 OR (ip_network_group_id IS NULL AND mp_group_name IS NULL AND '
                           'mp_group_provider IS NULL AND user_id IS NULL AND local_group_id IS NOT NULL)',
                           name='valid_local_group'),
        sa.CheckConstraint('type != 3 OR (ip_network_group_id IS NULL AND local_group_id IS NULL AND '
                           'user_id IS NULL AND mp_group_name IS NOT NULL AND mp_group_provider IS NOT NULL)',
                           name='valid_multipass_group'),
        sa.CheckConstraint('type != 5 OR (NOT full_access AND array_length(roles, 1) IS NULL)',
                           name='networks_read_only'),
        sa.CheckConstraint('type != 5 OR (local_group_id IS NULL AND mp_group_name IS NULL AND '
                           'mp_group_provider IS NULL AND user_id IS NULL AND ip_network_group_id IS NOT NULL)',
                           name='valid_network'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.categories.id']),
        sa.ForeignKeyConstraint(['ip_network_group_id'], ['indico.ip_network_groups.id']),
        sa.ForeignKeyConstraint(['local_group_id'], ['users.groups.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='categories'
    )
    op.create_index(op.f('ix_principals_category_id'), 'principals', ['category_id'], unique=False, schema='categories')
    op.create_index(op.f('ix_principals_ip_network_group_id'), 'principals', ['ip_network_group_id'], unique=False,
                    schema='categories')
    op.create_index(op.f('ix_principals_local_group_id'), 'principals', ['local_group_id'], unique=False,
                    schema='categories')
    op.create_index(op.f('ix_principals_mp_group_provider_mp_group_name'), 'principals',
                    ['mp_group_provider', 'mp_group_name'], unique=False, schema='categories')
    op.create_index(op.f('ix_principals_user_id'), 'principals', ['user_id'], unique=False, schema='categories')
    op.create_index('ix_uq_principals_local_group', 'principals', ['local_group_id', 'category_id'], unique=True,
                    schema='categories', postgresql_where=sa.text('type = 2'))
    op.create_index('ix_uq_principals_mp_group', 'principals', ['mp_group_provider', 'mp_group_name', 'category_id'],
                    unique=True, schema='categories', postgresql_where=sa.text('type = 3'))
    op.create_index('ix_uq_principals_user', 'principals', ['user_id', 'category_id'], unique=True, schema='categories',
                    postgresql_where=sa.text('type = 1'))


def downgrade():
    op.drop_table('principals', schema='categories')
    op.drop_table('categories', schema='categories')
