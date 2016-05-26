"""Sort criteria in generated CHECKs

Revision ID: 52bc314861ba
Revises: 258db7e5a3e5
Create Date: 2016-05-26 10:10:57.106337
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '52bc314861ba'
down_revision = '258db7e5a3e5'


def upgrade():
    op.execute("""
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_local_group;
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_multipass_group;
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_user;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_local_group;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_multipass_group;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_user;
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_local_group CHECK (((type <> 2) OR ((((mp_group_name IS NULL) AND (mp_group_provider IS NULL)) AND (user_id IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_multipass_group CHECK (((type <> 3) OR ((((local_group_id IS NULL) AND (user_id IS NULL)) AND (mp_group_name IS NOT NULL)) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_user CHECK (((type <> 1) OR ((((local_group_id IS NULL) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_local_group CHECK (((type <> 2) OR ((((mp_group_name IS NULL) AND (mp_group_provider IS NULL)) AND (user_id IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_multipass_group CHECK (((type <> 3) OR ((((local_group_id IS NULL) AND (user_id IS NULL)) AND (mp_group_name IS NOT NULL)) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_user CHECK (((type <> 1) OR ((((local_group_id IS NULL) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NOT NULL))));

        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_email;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_local_group;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_multipass_group;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_user;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_email;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_local_group;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_multipass_group;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_user;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_email;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_local_group;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_multipass_group;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_user;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_local_group;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_multipass_group;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_user;
        ALTER TABLE events.timetable_entries DROP CONSTRAINT ck_timetable_entries_valid_contribution;
        ALTER TABLE events.timetable_entries DROP CONSTRAINT ck_timetable_entries_valid_session_block;
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_email CHECK (((type <> 4) OR (((((local_group_id IS NULL) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NULL)) AND (email IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_local_group CHECK (((type <> 2) OR (((((email IS NULL) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_multipass_group CHECK (((type <> 3) OR (((((email IS NULL) AND (local_group_id IS NULL)) AND (user_id IS NULL)) AND (mp_group_name IS NOT NULL)) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_user CHECK (((type <> 1) OR (((((email IS NULL) AND (local_group_id IS NULL)) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_email CHECK (((type <> 4) OR (((((local_group_id IS NULL) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NULL)) AND (email IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_local_group CHECK (((type <> 2) OR (((((email IS NULL) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_multipass_group CHECK (((type <> 3) OR (((((email IS NULL) AND (local_group_id IS NULL)) AND (user_id IS NULL)) AND (mp_group_name IS NOT NULL)) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_user CHECK (((type <> 1) OR (((((email IS NULL) AND (local_group_id IS NULL)) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_email CHECK (((type <> 4) OR (((((local_group_id IS NULL) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NULL)) AND (email IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_local_group CHECK (((type <> 2) OR (((((email IS NULL) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_multipass_group CHECK (((type <> 3) OR (((((email IS NULL) AND (local_group_id IS NULL)) AND (user_id IS NULL)) AND (mp_group_name IS NOT NULL)) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_user CHECK (((type <> 1) OR (((((email IS NULL) AND (local_group_id IS NULL)) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_local_group CHECK (((type <> 2) OR ((((mp_group_name IS NULL) AND (mp_group_provider IS NULL)) AND (user_id IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_multipass_group CHECK (((type <> 3) OR ((((local_group_id IS NULL) AND (user_id IS NULL)) AND (mp_group_name IS NOT NULL)) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_user CHECK (((type <> 1) OR ((((local_group_id IS NULL) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NOT NULL))));
        ALTER TABLE events.timetable_entries ADD CONSTRAINT ck_timetable_entries_valid_contribution CHECK (((type <> 2) OR (((break_id IS NULL) AND (session_block_id IS NULL)) AND (contribution_id IS NOT NULL))));
        ALTER TABLE events.timetable_entries ADD CONSTRAINT ck_timetable_entries_valid_session_block CHECK (((type <> 1) OR (((break_id IS NULL) AND (contribution_id IS NULL)) AND (session_block_id IS NOT NULL))));

        ALTER TABLE indico.settings_principals DROP CONSTRAINT ck_settings_principals_valid_local_group;
        ALTER TABLE indico.settings_principals DROP CONSTRAINT ck_settings_principals_valid_multipass_group;
        ALTER TABLE indico.settings_principals DROP CONSTRAINT ck_settings_principals_valid_user;
        ALTER TABLE indico.settings_principals ADD CONSTRAINT ck_settings_principals_valid_local_group CHECK (((type <> 2) OR ((((mp_group_name IS NULL) AND (mp_group_provider IS NULL)) AND (user_id IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE indico.settings_principals ADD CONSTRAINT ck_settings_principals_valid_multipass_group CHECK (((type <> 3) OR ((((local_group_id IS NULL) AND (user_id IS NULL)) AND (mp_group_name IS NOT NULL)) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE indico.settings_principals ADD CONSTRAINT ck_settings_principals_valid_user CHECK (((type <> 1) OR ((((local_group_id IS NULL) AND (mp_group_name IS NULL)) AND (mp_group_provider IS NULL)) AND (user_id IS NOT NULL))));
    """)


def downgrade():
    op.execute("""
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_local_group;
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_multipass_group;
        ALTER TABLE attachments.attachment_principals DROP CONSTRAINT ck_attachment_principals_valid_user;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_local_group;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_multipass_group;
        ALTER TABLE attachments.folder_principals DROP CONSTRAINT ck_folder_principals_valid_user;
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_local_group CHECK (((type <> 2) OR ((((user_id IS NULL) AND (mp_group_provider IS NULL)) AND (mp_group_name IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_multipass_group CHECK (((type <> 3) OR ((((local_group_id IS NULL) AND (user_id IS NULL)) AND (mp_group_provider IS NOT NULL)) AND (mp_group_name IS NOT NULL))));
        ALTER TABLE attachments.attachment_principals ADD CONSTRAINT ck_attachment_principals_valid_user CHECK (((type <> 1) OR ((((local_group_id IS NULL) AND (mp_group_provider IS NULL)) AND (mp_group_name IS NULL)) AND (user_id IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_local_group CHECK (((type <> 2) OR ((((user_id IS NULL) AND (mp_group_provider IS NULL)) AND (mp_group_name IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_multipass_group CHECK (((type <> 3) OR ((((local_group_id IS NULL) AND (user_id IS NULL)) AND (mp_group_provider IS NOT NULL)) AND (mp_group_name IS NOT NULL))));
        ALTER TABLE attachments.folder_principals ADD CONSTRAINT ck_folder_principals_valid_user CHECK (((type <> 1) OR ((((local_group_id IS NULL) AND (mp_group_provider IS NULL)) AND (mp_group_name IS NULL)) AND (user_id IS NOT NULL))));

        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_email;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_local_group;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_multipass_group;
        ALTER TABLE events.contribution_principals DROP CONSTRAINT ck_contribution_principals_valid_user;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_email;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_local_group;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_multipass_group;
        ALTER TABLE events.principals DROP CONSTRAINT ck_principals_valid_user;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_email;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_local_group;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_multipass_group;
        ALTER TABLE events.session_principals DROP CONSTRAINT ck_session_principals_valid_user;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_local_group;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_multipass_group;
        ALTER TABLE events.settings_principals DROP CONSTRAINT ck_settings_principals_valid_user;
        ALTER TABLE events.timetable_entries DROP CONSTRAINT ck_timetable_entries_valid_contribution;
        ALTER TABLE events.timetable_entries DROP CONSTRAINT ck_timetable_entries_valid_session_block;
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_email CHECK (((type <> 4) OR (((((local_group_id IS NULL) AND (mp_group_provider IS NULL)) AND (mp_group_name IS NULL)) AND (user_id IS NULL)) AND (email IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_local_group CHECK (((type <> 2) OR (((((user_id IS NULL) AND (mp_group_provider IS NULL)) AND (email IS NULL)) AND (mp_group_name IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_multipass_group CHECK (((type <> 3) OR (((((local_group_id IS NULL) AND (user_id IS NULL)) AND (email IS NULL)) AND (mp_group_provider IS NOT NULL)) AND (mp_group_name IS NOT NULL))));
        ALTER TABLE events.contribution_principals ADD CONSTRAINT ck_contribution_principals_valid_user CHECK (((type <> 1) OR (((((local_group_id IS NULL) AND (mp_group_provider IS NULL)) AND (email IS NULL)) AND (mp_group_name IS NULL)) AND (user_id IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_email CHECK (((type <> 4) OR (((((local_group_id IS NULL) AND (mp_group_provider IS NULL)) AND (mp_group_name IS NULL)) AND (user_id IS NULL)) AND (email IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_local_group CHECK (((type <> 2) OR (((((user_id IS NULL) AND (mp_group_provider IS NULL)) AND (email IS NULL)) AND (mp_group_name IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_multipass_group CHECK (((type <> 3) OR (((((local_group_id IS NULL) AND (user_id IS NULL)) AND (email IS NULL)) AND (mp_group_provider IS NOT NULL)) AND (mp_group_name IS NOT NULL))));
        ALTER TABLE events.principals ADD CONSTRAINT ck_principals_valid_user CHECK (((type <> 1) OR (((((local_group_id IS NULL) AND (mp_group_provider IS NULL)) AND (email IS NULL)) AND (mp_group_name IS NULL)) AND (user_id IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_email CHECK (((type <> 4) OR (((((local_group_id IS NULL) AND (mp_group_provider IS NULL)) AND (mp_group_name IS NULL)) AND (user_id IS NULL)) AND (email IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_local_group CHECK (((type <> 2) OR (((((user_id IS NULL) AND (mp_group_provider IS NULL)) AND (email IS NULL)) AND (mp_group_name IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_multipass_group CHECK (((type <> 3) OR (((((local_group_id IS NULL) AND (user_id IS NULL)) AND (email IS NULL)) AND (mp_group_provider IS NOT NULL)) AND (mp_group_name IS NOT NULL))));
        ALTER TABLE events.session_principals ADD CONSTRAINT ck_session_principals_valid_user CHECK (((type <> 1) OR (((((local_group_id IS NULL) AND (mp_group_provider IS NULL)) AND (email IS NULL)) AND (mp_group_name IS NULL)) AND (user_id IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_local_group CHECK (((type <> 2) OR ((((user_id IS NULL) AND (mp_group_provider IS NULL)) AND (mp_group_name IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_multipass_group CHECK (((type <> 3) OR ((((local_group_id IS NULL) AND (user_id IS NULL)) AND (mp_group_provider IS NOT NULL)) AND (mp_group_name IS NOT NULL))));
        ALTER TABLE events.settings_principals ADD CONSTRAINT ck_settings_principals_valid_user CHECK (((type <> 1) OR ((((local_group_id IS NULL) AND (mp_group_provider IS NULL)) AND (mp_group_name IS NULL)) AND (user_id IS NOT NULL))));
        ALTER TABLE events.timetable_entries ADD CONSTRAINT ck_timetable_entries_valid_contribution CHECK (((type <> 2) OR (((session_block_id IS NULL) AND (break_id IS NULL)) AND (contribution_id IS NOT NULL))));
        ALTER TABLE events.timetable_entries ADD CONSTRAINT ck_timetable_entries_valid_session_block CHECK (((type <> 1) OR (((contribution_id IS NULL) AND (break_id IS NULL)) AND (session_block_id IS NOT NULL))));

        ALTER TABLE indico.settings_principals DROP CONSTRAINT ck_settings_principals_valid_local_group;
        ALTER TABLE indico.settings_principals DROP CONSTRAINT ck_settings_principals_valid_multipass_group;
        ALTER TABLE indico.settings_principals DROP CONSTRAINT ck_settings_principals_valid_user;
        ALTER TABLE indico.settings_principals ADD CONSTRAINT ck_settings_principals_valid_local_group CHECK (((type <> 2) OR ((((user_id IS NULL) AND (mp_group_provider IS NULL)) AND (mp_group_name IS NULL)) AND (local_group_id IS NOT NULL))));
        ALTER TABLE indico.settings_principals ADD CONSTRAINT ck_settings_principals_valid_multipass_group CHECK (((type <> 3) OR ((((local_group_id IS NULL) AND (user_id IS NULL)) AND (mp_group_provider IS NOT NULL)) AND (mp_group_name IS NOT NULL))));
        ALTER TABLE indico.settings_principals ADD CONSTRAINT ck_settings_principals_valid_user CHECK (((type <> 1) OR ((((local_group_id IS NULL) AND (mp_group_provider IS NULL)) AND (mp_group_name IS NULL)) AND (user_id IS NOT NULL))));
    """)
