"""Add annotations and converted_from_id to attachments, add case-insensitive collation

Revision ID: e4f49c197158
Revises: 869fb2760b41
Create Date: 2025-09-25 16:31:15.926991
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'e4f49c197158'
down_revision = '869fb2760b41'
branch_labels = None
depends_on = None

COLLATION_CASE_INSENSITIVE_DDL = '''
    CREATE COLLATION indico.case_insensitive (
        provider = icu,
        locale = 'und-u-ks-level2',
        deterministic = false
    )
'''


def upgrade():
    op.execute(COLLATION_CASE_INSENSITIVE_DDL)
    op.add_column('attachments', sa.Column('converted_from_id', sa.Integer(), nullable=True), schema='attachments')
    op.add_column(
        'attachments',
        sa.Column('annotations', postgresql.JSONB(), nullable=False, server_default='{}'),
        schema='attachments',
    )
    op.alter_column('attachments', 'annotations', server_default=None, schema='attachments')
    op.create_index(
        None,
        'attachments',
        ['converted_from_id'],
        unique=False,
        schema='attachments',
    )
    op.create_foreign_key(
        None,
        'attachments',
        'attachments',
        ['converted_from_id'],
        ['id'],
        source_schema='attachments',
        referent_schema='attachments',
    )


def downgrade():
    op.drop_column('attachments', 'annotations', schema='attachments')
    op.drop_column('attachments', 'converted_from_id', schema='attachments')
    op.execute('DROP COLLATION indico.case_insensitive')
