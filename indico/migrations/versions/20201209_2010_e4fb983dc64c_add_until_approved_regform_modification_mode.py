"""Add 'until approved' regform modification mode

Revision ID: e4fb983dc64c
Revises: 8d614ef75968
Create Date: 2020-12-09 20:10:12.155982
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'e4fb983dc64c'
down_revision = '8d614ef75968'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        ALTER TABLE "event_registration"."forms" DROP CONSTRAINT "ck_forms_valid_enum_modification_mode";
        ALTER TABLE "event_registration"."forms" ADD CONSTRAINT "ck_forms_valid_enum_modification_mode" CHECK ((modification_mode = ANY (ARRAY[1, 2, 3, 4])));
    ''')


def downgrade():
    op.execute('''
        UPDATE "event_registration"."forms" SET modification_mode = 3 WHERE modification_mode = 4;
        ALTER TABLE "event_registration"."forms" DROP CONSTRAINT "ck_forms_valid_enum_modification_mode";
        ALTER TABLE "event_registration"."forms" ADD CONSTRAINT "ck_forms_valid_enum_modification_mode" CHECK ((modification_mode = ANY (ARRAY[1, 2, 3])));
    ''')
