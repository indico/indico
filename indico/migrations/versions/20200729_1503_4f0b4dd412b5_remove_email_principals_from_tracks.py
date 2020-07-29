"""Remove email principals from tracks

Revision ID: 4f0b4dd412b5
Revises: 05f227f4b938
Create Date: 2020-07-29 15:03:47.509113
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '4f0b4dd412b5'
down_revision = '05f227f4b938'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_lowercase_email";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_email";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_category_role";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_enum_type";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_event_role";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_local_group";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_multipass_group";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_user";
        DROP INDEX "events"."ix_track_principals_email";
        DROP INDEX "events"."ix_uq_track_principals_email";
        ALTER TABLE "events"."track_principals" DROP COLUMN "email";
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_category_role" CHECK (((type <> 7) OR ((event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 6, 7])));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
    ''')


def downgrade():
    op.execute('''
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_category_role";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_enum_type";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_event_role";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_local_group";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_multipass_group";
        ALTER TABLE "events"."track_principals" DROP CONSTRAINT "ck_track_principals_valid_user";
        ALTER TABLE "events"."track_principals" ADD COLUMN "email" character varying;
        CREATE INDEX ix_track_principals_email ON events.track_principals USING btree (email);
        CREATE UNIQUE INDEX ix_uq_track_principals_email ON events.track_principals USING btree (email, track_id) WHERE (type = 4);
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_lowercase_email" CHECK (((email IS NULL) OR ((email)::text = lower((email)::text))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_email" CHECK (((type <> 4) OR ((category_role_id IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (email IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_category_role" CHECK (((type <> 7) OR ((email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (category_role_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3, 4, 6, 7])));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_event_role" CHECK (((type <> 6) OR ((category_role_id IS NULL) AND (email IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (event_role_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_local_group" CHECK (((type <> 2) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NULL) AND (local_group_id IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_multipass_group" CHECK (((type <> 3) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (user_id IS NULL) AND (mp_group_name IS NOT NULL) AND (mp_group_provider IS NOT NULL))));
        ALTER TABLE "events"."track_principals" ADD CONSTRAINT "ck_track_principals_valid_user" CHECK (((type <> 1) OR ((category_role_id IS NULL) AND (email IS NULL) AND (event_role_id IS NULL) AND (local_group_id IS NULL) AND (mp_group_name IS NULL) AND (mp_group_provider IS NULL) AND (user_id IS NOT NULL))));
    ''')
