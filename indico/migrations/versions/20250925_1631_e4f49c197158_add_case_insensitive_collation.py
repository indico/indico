"""Add case-insensitive collation

Revision ID: e4f49c197158
Revises: 43d2bff509c1
Create Date: 2025-09-25 16:31:15.926991
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'e4f49c197158'
down_revision = '43d2bff509c1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        CREATE COLLATION indico.case_insensitive (
            provider = icu,
            locale = 'und-u-ks-level2',
            deterministic = false
        );
    ''')


def downgrade():
    op.execute('DROP COLLATION indico.case_insensitive')
