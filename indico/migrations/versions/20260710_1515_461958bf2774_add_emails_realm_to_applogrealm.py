"""Add emails realm to AppLogRealm

Revision ID: 461958bf2774
Revises: e1e229910f7e
Create Date: 2026-02-18 13:46:48.862976
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '461958bf2774'
down_revision = 'e1e229910f7e'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('ck_logs_valid_enum_realm', 'logs', schema='indico')
    op.create_check_constraint('valid_enum_realm', 'logs', '(realm = ANY (ARRAY[1, 2, 3]))', schema='indico')


def downgrade():
    op.execute('UPDATE indico.logs SET realm = 2 WHERE realm = 3')
    op.drop_constraint('ck_logs_valid_enum_realm', 'logs', schema='indico')
    op.create_check_constraint('valid_enum_realm', 'logs', '(realm = ANY (ARRAY[1, 2]))', schema='indico')
