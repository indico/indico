"""Add file type column to PaperFile

Revision ID: 399da8ab2664
Revises: af9d03d7073c
Create Date: 2025-11-03 13:46:12.180621
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '399da8ab2664'
down_revision = 'af9d03d7073c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'files', sa.Column('file_type_id', sa.Integer(), nullable=True), schema='event_paper_reviewing'
    )
    op.create_index(None, 'files', ['file_type_id'], unique=False, schema='event_paper_reviewing')
    op.create_foreign_key(
        None,
        'files',
        'file_types',
        ['file_type_id'],
        ['id'],
        source_schema='event_paper_reviewing',
        referent_schema='event_paper_reviewing',
    )


def downgrade():
    op.drop_column('files', 'file_type_id', schema='event_paper_reviewing')
    # op.drop_column('file_types', 'filename_template', schema='event_paper_reviewing')
