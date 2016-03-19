"""Add attachment tables

Revision ID: 20392a888368
Revises: 27ed4c28ae7b
Create Date: 2015-06-24 11:27:03.169187
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.ddl import CreateSchema, DropSchema

from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.db.sqlalchemy.links import LinkType
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.attachments.models.attachments import AttachmentType


# revision identifiers, used by Alembic.
revision = '20392a888368'
down_revision = '27ed4c28ae7b'


def upgrade():
    op.execute(CreateSchema('attachments'))
    op.create_table(
        'folders',
        sa.Column('link_type', PyIntEnum(LinkType), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True, index=True),
        sa.Column('event_id', sa.Integer(), nullable=True, index=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('contribution_id', sa.String(), nullable=True),
        sa.Column('subcontribution_id', sa.String(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('is_always_visible', sa.Boolean(), nullable=False),
        sa.Column('protection_mode', PyIntEnum(ProtectionMode, exclude_values={ProtectionMode.public}), nullable=False),
        sa.Index(None, 'category_id', unique=True, postgresql_where=sa.text('link_type = 1 AND is_default')),
        sa.Index(None, 'event_id', unique=True, postgresql_where=sa.text('link_type = 2 AND is_default')),
        sa.Index(None, 'event_id', 'contribution_id', unique=True,
                 postgresql_where=sa.text('link_type = 3 AND is_default')),
        sa.Index(None, 'event_id', 'contribution_id', 'subcontribution_id', unique=True,
                 postgresql_where=sa.text('link_type = 4 AND is_default')),
        sa.Index(None, 'event_id', 'session_id', unique=True, postgresql_where=sa.text('link_type = 5 AND is_default')),
        sa.CheckConstraint('link_type != 1 OR (event_id IS NULL AND contribution_id IS NULL AND '
                           'subcontribution_id IS NULL AND session_id IS NULL AND category_id IS NOT NULL)',
                           name='valid_category_link'),
        sa.CheckConstraint('link_type != 2 OR (contribution_id IS NULL AND subcontribution_id IS NULL AND '
                           'category_id IS NULL AND session_id IS NULL AND event_id IS NOT NULL)',
                           name='valid_event_link'),
        sa.CheckConstraint('link_type != 3 OR (subcontribution_id IS NULL AND category_id IS NULL AND '
                           'session_id IS NULL AND event_id IS NOT NULL AND contribution_id IS NOT NULL)',
                           name='valid_contribution_link'),
        sa.CheckConstraint('link_type != 4 OR (category_id IS NULL AND session_id IS NULL AND event_id IS NOT NULL AND '
                           'contribution_id IS NOT NULL AND subcontribution_id IS NOT NULL)',
                           name='valid_subcontribution_link'),
        sa.CheckConstraint('link_type != 5 OR (contribution_id IS NULL AND subcontribution_id IS NULL AND '
                           'category_id IS NULL AND event_id IS NOT NULL AND session_id IS NOT NULL)',
                           name='valid_session_link'),
        sa.CheckConstraint('not (is_default and protection_mode != 1)', name='default_inheriting'),
        sa.CheckConstraint('is_default = (title IS NULL)', name='default_or_title'),
        sa.CheckConstraint('not (is_default and is_deleted)', name='default_not_deleted'),
        sa.PrimaryKeyConstraint('id'),
        schema='attachments'
    )
    op.create_table(
        'attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('folder_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('modified_dt', UTCDateTime, nullable=False),
        sa.Column('type', PyIntEnum(AttachmentType), nullable=False),
        sa.Column('link_url', sa.String(), nullable=True),
        sa.Column('file_id', sa.Integer(), nullable=True),
        sa.Column('protection_mode', PyIntEnum(ProtectionMode, exclude_values={ProtectionMode.public}),
                  nullable=False),
        sa.CheckConstraint('link_url IS NULL OR file_id IS NULL', name='link_or_file'),
        sa.CheckConstraint('type != 2 OR (link_url IS NOT NULL AND file_id IS NULL)', name='valid_link'),
        sa.ForeignKeyConstraint(['file_id'], ['attachments.files.id'], use_alter=True),
        sa.ForeignKeyConstraint(['folder_id'], ['attachments.folders.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='attachments'
    )
    op.create_table(
        'files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('attachment_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('storage_backend', sa.String(), nullable=False),
        sa.Column('storage_file_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['attachment_id'], ['attachments.attachments.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='attachments'
    )
    op.create_foreign_key(None,
                          'attachments', 'files',
                          ['file_id'], ['id'],
                          source_schema='attachments', referent_schema='attachments')
    op.create_table(
        'folder_principals',
        sa.Column('type', PyIntEnum(PrincipalType), nullable=True),
        sa.Column('mp_group_provider', sa.String(), nullable=True),
        sa.Column('mp_group_name', sa.String(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('folder_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('local_group_id', sa.Integer(), nullable=True, index=True),
        sa.CheckConstraint('type != 1 OR (local_group_id IS NULL AND mp_group_provider IS NULL '
                           'AND mp_group_name IS NULL AND user_id IS NOT NULL)', name='valid_user'),
        sa.CheckConstraint('type != 2 OR (user_id IS NULL AND mp_group_provider IS NULL AND mp_group_name IS NULL AND '
                           'local_group_id IS NOT NULL)', name='valid_local_group'),
        sa.CheckConstraint('type != 3 OR (local_group_id IS NULL AND user_id IS NULL AND '
                           'mp_group_provider IS NOT NULL AND mp_group_name IS NOT NULL)',
                           name='valid_multipass_group'),
        sa.ForeignKeyConstraint(['folder_id'], ['attachments.folders.id']),
        sa.ForeignKeyConstraint(['local_group_id'], ['users.groups.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='attachments'
    )
    op.create_index(None, 'folder_principals', ['mp_group_provider', 'mp_group_name'], schema='attachments')
    op.create_table(
        'attachment_principals',
        sa.Column('type', PyIntEnum(PrincipalType), nullable=True),
        sa.Column('mp_group_provider', sa.String(), nullable=True),
        sa.Column('mp_group_name', sa.String(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('attachment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('local_group_id', sa.Integer(), nullable=True, index=True),
        sa.CheckConstraint('type != 1 OR (local_group_id IS NULL AND mp_group_provider IS NULL '
                           'AND mp_group_name IS NULL AND user_id IS NOT NULL)', name='valid_user'),
        sa.CheckConstraint('type != 2 OR (user_id IS NULL AND mp_group_provider IS NULL AND mp_group_name IS NULL AND '
                           'local_group_id IS NOT NULL)', name='valid_local_group'),
        sa.CheckConstraint('type != 3 OR (local_group_id IS NULL AND user_id IS NULL AND '
                           'mp_group_provider IS NOT NULL AND mp_group_name IS NOT NULL)',
                           name='valid_multipass_group'),
        sa.ForeignKeyConstraint(['attachment_id'], ['attachments.attachments.id']),
        sa.ForeignKeyConstraint(['local_group_id'], ['users.groups.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='attachments'
    )
    op.create_index(None, 'attachment_principals', ['mp_group_provider', 'mp_group_name'], schema='attachments')


def downgrade():
    op.drop_constraint('fk_attachments_file_id_files', 'attachments', schema='attachments')
    op.drop_table('attachment_principals', schema='attachments')
    op.drop_table('folder_principals', schema='attachments')
    op.drop_table('files', schema='attachments')
    op.drop_table('attachments', schema='attachments')
    op.drop_table('folders', schema='attachments')
    op.execute(DropSchema('attachments'))
