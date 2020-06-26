"""Add registration form to event acls

Revision ID: b6dd0a4ed40d
Revises: c0fc1e46888b
Create Date: 2020-06-19 15:26:01.961716
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b6dd0a4ed40d'
down_revision = 'c0fc1e46888b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('attachment_principals', sa.Column('registration_form_id', sa.Integer()), schema='attachments')
    op.add_column('folder_principals', sa.Column('registration_form_id', sa.Integer()), schema='attachments')
    op.add_column('contribution_principals', sa.Column('registration_form_id', sa.Integer()), schema='events')
    op.add_column('principals', sa.Column('registration_form_id', sa.Integer(), nullable=True), schema='events')
    op.add_column('session_principals', sa.Column('registration_form_id', sa.Integer(), nullable=True), schema='events')
    op.create_index(None, 'attachment_principals', ['registration_form_id'], schema='attachments')
    op.create_index(None, 'folder_principals', ['registration_form_id'], schema='attachments')
    op.create_index(None, 'contribution_principals', ['registration_form_id'], schema='events')
    op.create_index(None, 'principals', ['registration_form_id'], schema='events')
    op.create_index(None, 'session_principals', ['registration_form_id'], schema='events')
    op.create_foreign_key(None, 'attachment_principals', 'forms',
                          ['registration_form_id'], ['id'],
                          source_schema='attachments', referent_schema='event_registration')
    op.create_foreign_key(None, 'folder_principals', 'forms',
                          ['registration_form_id'], ['id'],
                          source_schema='attachments', referent_schema='event_registration')
    op.create_foreign_key(None, 'contribution_principals', 'forms',
                          ['registration_form_id'], ['id'],
                          source_schema='events', referent_schema='event_registration')
    op.create_foreign_key(None, 'principals', 'forms',
                          ['registration_form_id'], ['id'],
                          source_schema='events', referent_schema='event_registration')
    op.create_foreign_key(None, 'session_principals', 'forms',
                          ['registration_form_id'], ['id'],
                          source_schema='events', referent_schema='event_registration')
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
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_registration_form" CHECK (((type <> 8) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (registration_form_id IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_registration_form" CHECK (((type <> 8) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (registration_form_id IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_registration_form_read_only" CHECK (((type <> 8) OR ((NOT full_access) AND (array_length(permissions, 1) IS NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_registration_form" CHECK (((type <> 8) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (registration_form_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_registration_form_read_only" CHECK (((type <> 8) OR ((NOT full_access) AND (array_length(permissions, 1) IS NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_registration_form" CHECK (((type <> 8) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (registration_form_id IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_registration_form_read_only" CHECK (((type <> 8) OR ((NOT full_access) AND (array_length(permissions, 1) IS NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_registration_form" CHECK (((type <> 8) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (registration_form_id IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_category_role" CHECK (((type <> 7) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 6, 7, 8])));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "attachments"."attachment_principals" ADD CONSTRAINT "ck_attachment_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_category_role" CHECK (((type <> 7) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 6, 7, 8])));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "attachments"."folder_principals" ADD CONSTRAINT "ck_folder_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_category_role" CHECK (((type <> 7) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_email" CHECK (((type <> 4) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 6, 7, 8])));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."contribution_principals" ADD CONSTRAINT "ck_contribution_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_category_role" CHECK (((type <> 7) OR ((email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_email" CHECK (((type <> 4) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 5, 6, 7, 8])));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (email IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_network" CHECK (((type <> 5) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (ip_network_group_id IS NOT NULL))));
        ALTER TABLE "events"."principals" ADD CONSTRAINT "ck_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (ip_network_group_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_category_role" CHECK (((type <> 7) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_email" CHECK (((type <> 4) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 6, 7, 8])));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."session_principals" ADD CONSTRAINT "ck_session_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (registration_form_id IS NULL) AND (user_id IS NOT NULL))));
    ''')


def downgrade():
    op.execute('''
        DELETE FROM attachments.attachment_principals WHERE type = 8;
        DELETE FROM attachments.folder_principals WHERE type = 8;
        DELETE FROM events.principals WHERE type = 8;
        DELETE FROM events.session_principals WHERE type = 8;
        DELETE FROM events.contribution_principals WHERE type = 8;
    ''')

    op.execute('''
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_registration_form";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_category_role";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_enum_type";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_event_role";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_local_group";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_multipass_group";
        ALTER TABLE "attachments"."attachment_principals" DROP CONSTRAINT "ck_attachment_principals_valid_user";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_registration_form";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_category_role";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_enum_type";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_event_role";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_local_group";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_multipass_group";
        ALTER TABLE "attachments"."folder_principals" DROP CONSTRAINT "ck_folder_principals_valid_user";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_registration_form_read_only";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_registration_form";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_category_role";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_email";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_enum_type";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_event_role";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_local_group";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_multipass_group";
        ALTER TABLE "events"."contribution_principals" DROP CONSTRAINT "ck_contribution_principals_valid_user";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_registration_form_read_only";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_registration_form";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_category_role";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_email";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_enum_type";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_event_role";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_local_group";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_multipass_group";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_network";
        ALTER TABLE "events"."principals" DROP CONSTRAINT "ck_principals_valid_user";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_registration_form_read_only";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_registration_form";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_category_role";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_email";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_enum_type";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_event_role";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_local_group";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_multipass_group";
        ALTER TABLE "events"."session_principals" DROP CONSTRAINT "ck_session_principals_valid_user";
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
    ''')

    op.drop_column('session_principals', 'registration_form_id', schema='events')
    op.drop_column('principals', 'registration_form_id', schema='events')
    op.drop_column('contribution_principals', 'registration_form_id', schema='events')
    op.drop_column('folder_principals', 'registration_form_id', schema='attachments')
    op.drop_column('attachment_principals', 'registration_form_id', schema='attachments')
