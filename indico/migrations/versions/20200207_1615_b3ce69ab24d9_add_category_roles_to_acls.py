"""Add category roles to acls

Revision ID: b3ce69ab24d9
Revises: 4d263fa78830
Create Date: 2020-02-07 16:15:04.168196
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b3ce69ab24d9'
down_revision = '4d263fa78830'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('attachment_principals', sa.Column('category_role_id', sa.Integer()), schema='attachments')
    op.add_column('folder_principals', sa.Column('category_role_id', sa.Integer()), schema='attachments')
    op.add_column('contribution_principals', sa.Column('category_role_id', sa.Integer()), schema='events')
    op.add_column('principals', sa.Column('category_role_id', sa.Integer(), nullable=True), schema='events')
    op.add_column('principals', sa.Column('category_role_id', sa.Integer(), nullable=True), schema='categories')
    op.add_column('session_principals', sa.Column('category_role_id', sa.Integer(), nullable=True), schema='events')
    op.add_column('track_principals', sa.Column('category_role_id', sa.Integer(), nullable=True), schema='events')
    op.add_column('settings_principals', sa.Column('category_role_id', sa.Integer(), nullable=True), schema='events')
    op.create_index(None, 'attachment_principals', ['category_role_id'], schema='attachments')
    op.create_index(None, 'folder_principals', ['category_role_id'], schema='attachments')
    op.create_index(None, 'contribution_principals', ['category_role_id'], schema='events')
    op.create_index(None, 'principals', ['category_role_id'], schema='events')
    op.create_index(None, 'principals', ['category_role_id'], schema='categories')
    op.create_index(None, 'session_principals', ['category_role_id'], schema='events')
    op.create_index(None, 'settings_principals', ['category_role_id'], schema='events')
    op.create_index(None, 'track_principals', ['category_role_id'], schema='events')
    op.create_foreign_key(None, 'attachment_principals', 'roles',
                          ['category_role_id'], ['id'],
                          source_schema='attachments', referent_schema='categories')
    op.create_foreign_key(None, 'folder_principals', 'roles',
                          ['category_role_id'], ['id'],
                          source_schema='attachments', referent_schema='categories')
    op.create_foreign_key(None, 'contribution_principals', 'roles',
                          ['category_role_id'], ['id'],
                          source_schema='events', referent_schema='categories')
    op.create_foreign_key(None, 'principals', 'roles',
                          ['category_role_id'], ['id'],
                          source_schema='events', referent_schema='categories')
    op.create_foreign_key(None, 'principals', 'roles',
                          ['category_role_id'], ['id'],
                          source_schema='categories', referent_schema='categories')
    op.create_foreign_key(None, 'session_principals', 'roles',
                          ['category_role_id'], ['id'],
                          source_schema='events', referent_schema='categories')
    op.create_foreign_key(None, 'settings_principals', 'roles',
                          ['category_role_id'], ['id'],
                          source_schema='events', referent_schema='categories')
    op.create_foreign_key(None, 'track_principals', 'roles',
                          ['category_role_id'], ['id'],
                          source_schema='events', referent_schema='categories')

    op.execute('''
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_enum_type";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_event_role";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_local_group";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_multipass_group";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_user";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_enum_type";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_event_role";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_local_group";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_multipass_group";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_user";
        ALTER TABLE "categories"."principals" DROP CONSTRAINT "ck_principals_valid_enum_type";
        ALTER TABLE "categories"."principals" DROP CONSTRAINT "ck_principals_valid_local_group";
        ALTER TABLE "categories"."principals" DROP CONSTRAINT "ck_principals_valid_multipass_group";
        ALTER TABLE "categories"."principals" DROP CONSTRAINT "ck_principals_valid_network";
        ALTER TABLE "categories"."principals" DROP CONSTRAINT "ck_principals_valid_user";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_email";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_enum_type";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_event_role";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_local_group";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_multipass_group";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_user";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_email";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_enum_type";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_event_role";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_local_group";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_multipass_group";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_network";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_user";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_email";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_enum_type";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_event_role";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_local_group";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_multipass_group";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_user";
        ALTER TABLE "events"."settings_principals" DROP CONSTRAINT "ck_settings_principals_valid_enum_type";
        ALTER TABLE "events"."settings_principals" DROP CONSTRAINT "ck_settings_principals_valid_event_role";
        ALTER TABLE "events"."settings_principals" DROP CONSTRAINT "ck_settings_principals_valid_local_group";
        ALTER TABLE "events"."settings_principals" DROP CONSTRAINT "ck_settings_principals_valid_multipass_group";
        ALTER TABLE "events"."settings_principals" DROP CONSTRAINT "ck_settings_principals_valid_user";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_email";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_enum_type";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_event_role";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_local_group";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_multipass_group";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_user";
        ALTER TABLE "categories"."principals" ADD CONSTRAINT "ck_principals_valid_category_role" CHECK (((type <> 7) OR ((ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "categories"."principals" ADD CONSTRAINT "ck_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 5, 7])));
        ALTER TABLE "categories"."principals" ADD CONSTRAINT "ck_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "categories"."principals" ADD CONSTRAINT "ck_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "categories"."principals" ADD CONSTRAINT "ck_principals_valid_network" CHECK (((type <> 5) OR ((category_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (ip_network_group_id IS NOT NULL))));
        ALTER TABLE "categories"."principals" ADD CONSTRAINT "ck_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_category_role" CHECK (((type <> 7) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 6, 7])));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_category_role" CHECK (((type <> 7) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 6, 7])));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_category_role" CHECK (((type <> 7) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_email" CHECK (((type <> 4) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 6, 7])));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_category_role" CHECK (((type <> 7) OR ((email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_email" CHECK (((type <> 4) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 5, 6, 7])));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (email IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_network" CHECK (((type <> 5) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (ip_network_group_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_category_role" CHECK (((type <> 7) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_email" CHECK (((type <> 4) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 6, 7])));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."settings_principals" ADD CONSTRAINT "ck_settings_principals_valid_category_role" CHECK (((type <> 7) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "events"."settings_principals" ADD CONSTRAINT "ck_settings_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 6, 7])));
        ALTER TABLE "events"."settings_principals" ADD CONSTRAINT "ck_settings_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."settings_principals" ADD CONSTRAINT "ck_settings_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."settings_principals" ADD CONSTRAINT "ck_settings_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."settings_principals" ADD CONSTRAINT "ck_settings_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_category_role" CHECK (((type <> 7) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_email" CHECK (((type <> 4) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 6, 7])));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
    ''')


def downgrade():
    op.execute('''
        DELETE FROM attachments.attachment_principals WHERE type = 7;
        DELETE FROM attachments.folder_principals WHERE type = 7;
        DELETE FROM events.principals WHERE type = 7;
        DELETE FROM events.settings_principals WHERE type = 7;
        DELETE FROM events.session_principals WHERE type = 7;
        DELETE FROM events.contribution_principals WHERE type = 7;
        DELETE FROM events.track_principals WHERE type = 7;
        DELETE FROM categories.principals WHERE type = 7;
    ''')

    op.execute('''
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_category_role";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_enum_type";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_event_role";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_local_group";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_multipass_group";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_user";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_category_role";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_enum_type";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_event_role";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_local_group";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_multipass_group";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_user";
        ALTER TABLE "categories"."principals" DROP CONSTRAINT "ck_principals_valid_category_role";
        ALTER TABLE "categories"."principals" DROP CONSTRAINT "ck_principals_valid_enum_type";
        ALTER TABLE "categories"."principals" DROP CONSTRAINT "ck_principals_valid_local_group";
        ALTER TABLE "categories"."principals" DROP CONSTRAINT "ck_principals_valid_multipass_group";
        ALTER TABLE "categories"."principals" DROP CONSTRAINT "ck_principals_valid_network";
        ALTER TABLE "categories"."principals" DROP CONSTRAINT "ck_principals_valid_user";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_category_role";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_email";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_enum_type";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_event_role";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_local_group";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_multipass_group";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_user";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_category_role";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_email";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_enum_type";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_event_role";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_local_group";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_multipass_group";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_network";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_user";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_category_role";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_email";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_enum_type";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_event_role";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_local_group";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_multipass_group";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_user";
        ALTER TABLE "events"."settings_principals" DROP CONSTRAINT "ck_settings_principals_valid_category_role";
        ALTER TABLE "events"."settings_principals" DROP CONSTRAINT "ck_settings_principals_valid_enum_type";
        ALTER TABLE "events"."settings_principals" DROP CONSTRAINT "ck_settings_principals_valid_event_role";
        ALTER TABLE "events"."settings_principals" DROP CONSTRAINT "ck_settings_principals_valid_local_group";
        ALTER TABLE "events"."settings_principals" DROP CONSTRAINT "ck_settings_principals_valid_multipass_group";
        ALTER TABLE "events"."settings_principals" DROP CONSTRAINT "ck_settings_principals_valid_user";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_category_role";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_email";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_enum_type";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_event_role";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_local_group";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_multipass_group";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_user";
        ALTER TABLE "categories"."principals" ADD CONSTRAINT "ck_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 5])));
        ALTER TABLE "categories"."principals" ADD CONSTRAINT "ck_principals_valid_local_group" CHECK (((type <> 2) OR ((ip_network_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "categories"."principals" ADD CONSTRAINT "ck_principals_valid_multipass_group" CHECK (((type <> 3) OR ((ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "categories"."principals" ADD CONSTRAINT "ck_principals_valid_network" CHECK (((type <> 5) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (ip_network_group_id IS NOT NULL))));
        ALTER TABLE "categories"."principals" ADD CONSTRAINT "ck_principals_valid_user" CHECK (((type <> 1) OR ((ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 6])));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_event_role" CHECK (((type <> 6) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_local_group" CHECK (((type <> 2) OR ((event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_multipass_group" CHECK (((type <> 3) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_user" CHECK (((type <> 1) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 6])));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_event_role" CHECK (((type <> 6) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_local_group" CHECK (((type <> 2) OR ((event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_multipass_group" CHECK (((type <> 3) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_user" CHECK (((type <> 1) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_email" CHECK (((type <> 4) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 6])));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_event_role" CHECK (((type <> 6) OR ((email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_local_group" CHECK (((type <> 2) OR ((email IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_multipass_group" CHECK (((type <> 3) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_user" CHECK (((type <> 1) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_email" CHECK (((type <> 4) OR ((event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 5, 6])));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_event_role" CHECK (((type <> 6) OR ((email IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_local_group" CHECK (((type <> 2) OR ((email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_multipass_group" CHECK (((type <> 3) OR ((email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_network" CHECK (((type <> 5) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (ip_network_group_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_user" CHECK (((type <> 1) OR ((email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_email" CHECK (((type <> 4) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 6])));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_event_role" CHECK (((type <> 6) OR ((email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_local_group" CHECK (((type <> 2) OR ((email IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_multipass_group" CHECK (((type <> 3) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_user" CHECK (((type <> 1) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."settings_principals" ADD CONSTRAINT "ck_settings_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 6])));
        ALTER TABLE "events"."settings_principals" ADD CONSTRAINT "ck_settings_principals_valid_event_role" CHECK (((type <> 6) OR ((local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."settings_principals" ADD CONSTRAINT "ck_settings_principals_valid_local_group" CHECK (((type <> 2) OR ((event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."settings_principals" ADD CONSTRAINT "ck_settings_principals_valid_multipass_group" CHECK (((type <> 3) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."settings_principals" ADD CONSTRAINT "ck_settings_principals_valid_user" CHECK (((type <> 1) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_email" CHECK (((type <> 4) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 6])));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_event_role" CHECK (((type <> 6) OR ((email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_local_group" CHECK (((type <> 2) OR ((email IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_multipass_group" CHECK (((type <> 3) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_user" CHECK (((type <> 1) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
    ''')

    op.drop_column('track_principals', 'category_role_id', schema='events')
    op.drop_column('settings_principals', 'category_role_id', schema='events')
    op.drop_column('session_principals', 'category_role_id', schema='events')
    op.drop_column('principals', 'category_role_id', schema='events')
    op.drop_column('principals', 'category_role_id', schema='categories')
    op.drop_column('contribution_principals', 'category_role_id', schema='events')
    op.drop_column('folder_principals', 'category_role_id', schema='attachments')
    op.drop_column('attachment_principals', 'category_role_id', schema='attachments')
