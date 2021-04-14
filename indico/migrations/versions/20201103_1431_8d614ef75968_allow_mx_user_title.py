"""Allow mx user title

Revision ID: 8d614ef75968
Revises: f37d509e221c
Create Date: 2020-11-03 14:31:44.639447
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '8d614ef75968'
down_revision = 'f37d509e221c'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        ALTER TABLE "event_abstracts"."abstract_person_links" DROP CONSTRAINT "ck_abstract_person_links_valid_enum_title";
        ALTER TABLE "events"."contribution_person_links" DROP CONSTRAINT "ck_contribution_person_links_valid_enum_title";
        ALTER TABLE "events"."event_person_links" DROP CONSTRAINT "ck_event_person_links_valid_enum_title";
        ALTER TABLE "events"."persons" DROP CONSTRAINT "ck_persons_valid_enum_title";
        ALTER TABLE "events"."session_block_person_links" DROP CONSTRAINT "ck_session_block_person_links_valid_enum_title";
        ALTER TABLE "events"."subcontribution_person_links" DROP CONSTRAINT "ck_subcontribution_person_links_valid_enum_title";
        ALTER TABLE "users"."users" DROP CONSTRAINT "ck_users_valid_enum_title";
        ALTER TABLE "event_abstracts"."abstract_person_links" ADD CONSTRAINT "ck_abstract_person_links_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5, 6])));
        ALTER TABLE "events"."contribution_person_links" ADD CONSTRAINT "ck_contribution_person_links_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5, 6])));
        ALTER TABLE "events"."event_person_links" ADD CONSTRAINT "ck_event_person_links_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5, 6])));
        ALTER TABLE "events"."persons" ADD CONSTRAINT "ck_persons_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5, 6])));
        ALTER TABLE "events"."session_block_person_links" ADD CONSTRAINT "ck_session_block_person_links_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5, 6])));
        ALTER TABLE "events"."subcontribution_person_links" ADD CONSTRAINT "ck_subcontribution_person_links_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5, 6])));
        ALTER TABLE "users"."users" ADD CONSTRAINT "ck_users_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5, 6])));
    ''')


def downgrade():
    op.execute('''
        UPDATE "event_abstracts"."abstract_person_links" SET title = 0 WHERE title = 6;
        UPDATE "events"."contribution_person_links" SET title = 0 WHERE title = 6;
        UPDATE "events"."event_person_links" SET title = 0 WHERE title = 6;
        UPDATE "events"."persons" SET title = 0 WHERE title = 6;
        UPDATE "events"."session_block_person_links" SET title = 0 WHERE title = 6;
        UPDATE "events"."subcontribution_person_links" SET title = 0 WHERE title = 6;
        UPDATE "users"."users" SET title = 0 WHERE title = 6;
    ''')
    op.execute('''
        ALTER TABLE "event_abstracts"."abstract_person_links" DROP CONSTRAINT "ck_abstract_person_links_valid_enum_title";
        ALTER TABLE "events"."contribution_person_links" DROP CONSTRAINT "ck_contribution_person_links_valid_enum_title";
        ALTER TABLE "events"."event_person_links" DROP CONSTRAINT "ck_event_person_links_valid_enum_title";
        ALTER TABLE "events"."persons" DROP CONSTRAINT "ck_persons_valid_enum_title";
        ALTER TABLE "events"."session_block_person_links" DROP CONSTRAINT "ck_session_block_person_links_valid_enum_title";
        ALTER TABLE "events"."subcontribution_person_links" DROP CONSTRAINT "ck_subcontribution_person_links_valid_enum_title";
        ALTER TABLE "users"."users" DROP CONSTRAINT "ck_users_valid_enum_title";
        ALTER TABLE "event_abstracts"."abstract_person_links" ADD CONSTRAINT "ck_abstract_person_links_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5])));
        ALTER TABLE "events"."contribution_person_links" ADD CONSTRAINT "ck_contribution_person_links_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5])));
        ALTER TABLE "events"."event_person_links" ADD CONSTRAINT "ck_event_person_links_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5])));
        ALTER TABLE "events"."persons" ADD CONSTRAINT "ck_persons_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5])));
        ALTER TABLE "events"."session_block_person_links" ADD CONSTRAINT "ck_session_block_person_links_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5])));
        ALTER TABLE "events"."subcontribution_person_links" ADD CONSTRAINT "ck_subcontribution_person_links_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5])));
        ALTER TABLE "users"."users" ADD CONSTRAINT "ck_users_valid_enum_title" CHECK ((title = ANY (ARRAY[0, 1, 2, 3, 4, 5])));
    ''')
