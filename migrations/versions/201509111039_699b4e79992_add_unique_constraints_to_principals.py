"""Add UNIQUE constraints to principals

Revision ID: 699b4e79992
Revises: 47977407fa2b
Create Date: 2015-09-11 10:39:48.972452
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '699b4e79992'
down_revision = '47977407fa2b'


def upgrade():
    op.create_index('ix_uq_attachment_principals_local_group', 'attachment_principals',
                    ['local_group_id', 'attachment_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('type = 2'))
    op.create_index('ix_uq_attachment_principals_mp_group', 'attachment_principals',
                    ['mp_group_provider', 'mp_group_name', 'attachment_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('type = 3'))
    op.create_index('ix_uq_attachment_principals_user', 'attachment_principals',
                    ['user_id', 'attachment_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('type = 1'))
    op.create_index('ix_uq_folder_principals_local_group', 'folder_principals',
                    ['local_group_id', 'folder_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('type = 2'))
    op.create_index('ix_uq_folder_principals_mp_group', 'folder_principals',
                    ['mp_group_provider', 'mp_group_name', 'folder_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('type = 3'))
    op.create_index('ix_uq_folder_principals_user', 'folder_principals',
                    ['user_id', 'folder_id'], unique=True, schema='attachments',
                    postgresql_where=sa.text('type = 1'))
    op.create_index('ix_uq_settings_principals_local_group', 'settings_principals',
                    ['local_group_id', 'module', 'name', 'event_id'], unique=True, schema='events',
                    postgresql_where=sa.text('type = 2'))
    op.create_index('ix_uq_settings_principals_mp_group', 'settings_principals',
                    ['mp_group_provider', 'mp_group_name', 'module', 'name', 'event_id'], unique=True, schema='events',
                    postgresql_where=sa.text('type = 3'))
    op.create_index('ix_uq_settings_principals_user', 'settings_principals',
                    ['user_id', 'module', 'name', 'event_id'], unique=True, schema='events',
                    postgresql_where=sa.text('type = 1'))
    op.create_index('ix_uq_settings_principals_local_group', 'settings_principals',
                    ['local_group_id', 'module', 'name'], unique=True, schema='indico',
                    postgresql_where=sa.text('type = 2'))
    op.create_index('ix_uq_settings_principals_mp_group', 'settings_principals',
                    ['mp_group_provider', 'mp_group_name', 'module', 'name'], unique=True, schema='indico',
                    postgresql_where=sa.text('type = 3'))
    op.create_index('ix_uq_settings_principals_user', 'settings_principals',
                    ['user_id', 'module', 'name'], unique=True, schema='indico',
                    postgresql_where=sa.text('type = 1'))


def downgrade():
    op.drop_index('ix_uq_settings_principals_user', table_name='settings_principals', schema='indico')
    op.drop_index('ix_uq_settings_principals_mp_group', table_name='settings_principals', schema='indico')
    op.drop_index('ix_uq_settings_principals_local_group', table_name='settings_principals', schema='indico')
    op.drop_index('ix_uq_settings_principals_user', table_name='settings_principals', schema='events')
    op.drop_index('ix_uq_settings_principals_mp_group', table_name='settings_principals', schema='events')
    op.drop_index('ix_uq_settings_principals_local_group', table_name='settings_principals', schema='events')
    op.drop_index('ix_uq_folder_principals_user', table_name='folder_principals', schema='attachments')
    op.drop_index('ix_uq_folder_principals_mp_group', table_name='folder_principals', schema='attachments')
    op.drop_index('ix_uq_folder_principals_local_group', table_name='folder_principals', schema='attachments')
    op.drop_index('ix_uq_attachment_principals_user', table_name='attachment_principals', schema='attachments')
    op.drop_index('ix_uq_attachment_principals_mp_group', table_name='attachment_principals', schema='attachments')
    op.drop_index('ix_uq_attachment_principals_local_group', table_name='attachment_principals', schema='attachments')
