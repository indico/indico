"""Add slides as EditableType

Revision ID: 56a26a721717
Revises: a3295d628e3b
Create Date: 2020-03-19 16:05:28.021616
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '56a26a721717'
down_revision = 'a3295d628e3b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        ALTER TABLE "event_editing"."editables" DROP CONSTRAINT "ck_editables_valid_enum_type";
        ALTER TABLE "event_editing"."editables" ADD CONSTRAINT "ck_editables_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2, 3])));
    ''')


def downgrade():
    op.execute('''
        ALTER TABLE "event_editing"."editables" DROP CONSTRAINT "ck_editables_valid_enum_type";
        ALTER TABLE "event_editing"."editables" ADD CONSTRAINT "ck_editables_valid_enum_type" CHECK ((type = ANY (ARRAY[1, 2])));
    ''')
