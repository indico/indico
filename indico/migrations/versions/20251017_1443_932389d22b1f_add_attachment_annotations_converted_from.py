"""Add attachment annotations + converted_from

Revision ID: 932389d22b1f
Revises: 43d2bff509c1
Create Date: 2025-10-17 14:43:47.050322
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '932389d22b1f'
down_revision = '43d2bff509c1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('attachments', sa.Column('converted_from_id', sa.Integer(), nullable=True), schema='attachments')
    op.add_column('attachments', sa.Column('annotations', postgresql.JSONB(), nullable=False, server_default='{}'),
                  schema='attachments')
    op.alter_column('attachments', 'annotations', server_default=None, schema='attachments')
    op.create_index(None, 'attachments', ['converted_from_id'], schema='attachments')
    op.create_foreign_key(None, 'attachments', 'attachments', ['converted_from_id'], ['id'],
                          source_schema='attachments', referent_schema='attachments')


def downgrade():
    op.drop_column('attachments', 'annotations', schema='attachments')
    op.drop_column('attachments', 'converted_from_id', schema='attachments')
