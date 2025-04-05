"""Add new realm to UserLogRealm

Revision ID: a5b6d7237997
Revises: 4615aff776e0
Create Date: 2025-04-03 15:13:05.723534
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'a5b6d7237997'
down_revision = '4615aff776e0'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('ck_logs_valid_enum_realm', 'logs', schema='users')
    op.create_check_constraint('valid_enum_realm', 'logs',
                               '(realm = ANY (ARRAY[1, 2, 3]))', schema='users')


def downgrade():
    op.drop_constraint('ck_logs_valid_enum_realm', 'logs', schema='users')
    op.create_check_constraint('valid_enum_realm', 'logs',
                               '(realm = ANY (ARRAY[1, 2]))', schema='users')
