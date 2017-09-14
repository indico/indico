"""Add event roles to acls

Revision ID: 640584a3987e
Revises: f1eee7b4880a
Create Date: 2017-09-05 15:21:13.323181
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '640584a3987e'
down_revision = 'f1eee7b4880a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('attachment_principals', sa.Column('event_role_id', sa.Integer()), schema='attachments')
    op.add_column('folder_principals', sa.Column('event_role_id', sa.Integer()), schema='attachments')
    op.add_column('contribution_principals', sa.Column('event_role_id', sa.Integer()), schema='events')
    op.add_column('principals', sa.Column('event_role_id', sa.Integer()), schema='events')
    op.add_column('session_principals', sa.Column('event_role_id', sa.Integer()), schema='events')
    op.add_column('settings_principals', sa.Column('event_role_id', sa.Integer()), schema='events')
    op.create_index(None, 'attachment_principals', ['event_role_id'], schema='attachments')
    op.create_index(None, 'folder_principals', ['event_role_id'], schema='attachments')
    op.create_index(None, 'contribution_principals', ['event_role_id'], schema='events')
    op.create_index(None, 'principals', ['event_role_id'], schema='events')
    op.create_index(None, 'session_principals', ['event_role_id'], schema='events')
    op.create_index(None, 'settings_principals', ['event_role_id'], schema='events')
    op.create_foreign_key(None, 'attachment_principals', 'roles',
                          ['event_role_id'], ['id'],
                          source_schema='attachments', referent_schema='events')
    op.create_foreign_key(None, 'folder_principals', 'roles',
                          ['event_role_id'], ['id'],
                          source_schema='attachments', referent_schema='events')
    op.create_foreign_key(None, 'contribution_principals', 'roles',
                          ['event_role_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.create_foreign_key(None, 'principals', 'roles',
                          ['event_role_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.create_foreign_key(None, 'session_principals', 'roles',
                          ['event_role_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.create_foreign_key(None, 'settings_principals', 'roles',
                          ['event_role_id'], ['id'],
                          source_schema='events', referent_schema='events')
    op.execute('''
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_enum_type;
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_local_group;
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_multipass_group;
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_user;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_enum_type;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_local_group;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_multipass_group;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_user;
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_enum_type CHECK ((type = ANY (ARRAY[1, 2, 3, 6])));
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_event_role CHECK (((type <> 6) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_local_group CHECK (((type <> 2) OR ((event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_multipass_group CHECK (((type <> 3) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_user CHECK (((type <> 1) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_enum_type CHECK ((type = ANY (ARRAY[1, 2, 3, 6])));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_event_role CHECK (((type <> 6) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_local_group CHECK (((type <> 2) OR ((event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_multipass_group CHECK (((type <> 3) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_user CHECK (((type <> 1) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_email;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_enum_type;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_local_group;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_multipass_group;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_user;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_email;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_enum_type;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_local_group;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_multipass_group;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_network;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_user;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_email;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_enum_type;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_local_group;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_multipass_group;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_user;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_enum_type;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_local_group;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_multipass_group;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_user;
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_email CHECK (((type <> 4) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_enum_type CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 6])));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_event_role CHECK (((type <> 6) OR ((email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_local_group CHECK (((type <> 2) OR ((email IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_multipass_group CHECK (((type <> 3) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_user CHECK (((type <> 1) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_email CHECK (((type <> 4) OR ((event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_enum_type CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 5, 6])));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_event_role CHECK (((type <> 6) OR ((email IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_local_group CHECK (((type <> 2) OR ((email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_multipass_group CHECK (((type <> 3) OR ((email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_network CHECK (((type <> 5) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (ip_network_group_id IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_user CHECK (((type <> 1) OR ((email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_email CHECK (((type <> 4) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_enum_type CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 6])));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_event_role CHECK (((type <> 6) OR ((email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_local_group CHECK (((type <> 2) OR ((email IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_multipass_group CHECK (((type <> 3) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_user CHECK (((type <> 1) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_enum_type CHECK ((type = ANY (ARRAY[1, 2, 3, 6])));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_event_role CHECK (((type <> 6) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_local_group CHECK (((type <> 2) OR ((event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_multipass_group CHECK (((type <> 3) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_user CHECK (((type <> 1) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
    ''')


def downgrade():
    op.execute('''
        DELETE FROM attachments.attachment_principals WHERE type = 6;
        DELETE FROM attachments.folder_principals WHERE type = 6;
        DELETE FROM events.principals WHERE type = 6;
        DELETE FROM events.settings_principals WHERE type = 6;
        DELETE FROM events.session_principals WHERE type = 6;
        DELETE FROM events.contribution_principals WHERE type = 6;
    ''')
    op.execute('''
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_enum_type;
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_event_role;
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_local_group;
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_multipass_group;
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_user;
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT fk_attachment_principals_event_role_id_roles;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_enum_type;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_event_role;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_local_group;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_multipass_group;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_user;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT fk_folder_principals_event_role_id_roles;
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_enum_type CHECK ((type = ANY (ARRAY[1, 2, 3])));
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_local_group CHECK (((type <> 2) OR ((mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_multipass_group CHECK (((type <> 3) OR ((local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_user CHECK (((type <> 1) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_enum_type CHECK ((type = ANY (ARRAY[1, 2, 3])));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_local_group CHECK (((type <> 2) OR ((mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_multipass_group CHECK (((type <> 3) OR ((local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_user CHECK (((type <> 1) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_email;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_enum_type;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_event_role;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_local_group;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_multipass_group;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_user;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT fk_contribution_principals_event_role_id_roles;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_email;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_enum_type;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_event_role;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_local_group;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_multipass_group;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_network;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_user;
        ALTER TABLE events.principals DROP CONSTRAINT fk_principals_event_role_id_roles;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_email;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_enum_type;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_event_role;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_local_group;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_multipass_group;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_user;
        ALTER TABLE events.session_principals DROP CONSTRAINT fk_session_principals_event_role_id_roles;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_enum_type;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_event_role;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_local_group;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_multipass_group;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_user;
        ALTER TABLE events.settings_principals DROP CONSTRAINT fk_settings_principals_event_role_id_roles;
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_email CHECK (((type <> 4) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_enum_type CHECK ((type = ANY (ARRAY[1, 2, 3, 4])));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_local_group CHECK (((type <> 2) OR ((email IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_multipass_group CHECK (((type <> 3) OR ((email IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_user CHECK (((type <> 1) OR ((email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_email CHECK (((type <> 4) OR ((ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_enum_type CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 5])));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_local_group CHECK (((type <> 2) OR ((email IS NULL) AND (ip_network_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_multipass_group CHECK (((type <> 3) OR ((email IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_network CHECK (((type <> 5) OR ((email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (ip_network_group_id IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_user CHECK (((type <> 1) OR ((email IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_email CHECK (((type <> 4) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_enum_type CHECK ((type = ANY (ARRAY[1, 2, 3, 4])));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_local_group CHECK (((type <> 2) OR ((email IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_multipass_group CHECK (((type <> 3) OR ((email IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_user CHECK (((type <> 1) OR ((email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_enum_type CHECK ((type = ANY (ARRAY[1, 2, 3])));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_local_group CHECK (((type <> 2) OR ((mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_multipass_group CHECK (((type <> 3) OR ((local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_user CHECK (((type <> 1) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
    ''')
    op.drop_column('settings_principals', 'event_role_id', schema='events')
    op.drop_column('session_principals', 'event_role_id', schema='events')
    op.drop_column('principals', 'event_role_id', schema='events')
    op.drop_column('contribution_principals', 'event_role_id', schema='events')
    op.drop_column('folder_principals', 'event_role_id', schema='attachments')
    op.drop_column('attachment_principals', 'event_role_id', schema='attachments')
