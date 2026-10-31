"""sync editing file types to paper file types

Revision ID: 40e811da06f9
Revises: af9d03d7073c
Create Date: 2026-03-10 12:02:58.599843
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '40e811da06f9'
down_revision = 'af9d03d7073c'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('ix_uq_file_types_event_id_name_lower', table_name='file_types', schema='event_paper_reviewing')
    op.add_column('file_types', sa.Column('source_editing_file_type_id', sa.Integer(), nullable=True),
                  schema='event_paper_reviewing')
    op.create_index('ix_file_types_source_editing_file_type_id', 'file_types', ['source_editing_file_type_id'],
                    unique=False, schema='event_paper_reviewing')
    op.create_index(
        'ix_uq_file_types_event_id_name_lower',
        'file_types',
        ['event_id', sa.text('lower(name)')],
        unique=True,
        schema='event_paper_reviewing',
        postgresql_where=sa.text('source_editing_file_type_id IS NULL')
    )
    op.create_index(
        'ix_uq_file_types_event_id_source_editing_file_type_id',
        'file_types',
        ['event_id', 'source_editing_file_type_id'],
        unique=True,
        schema='event_paper_reviewing',
        postgresql_where=sa.text('source_editing_file_type_id IS NOT NULL')
    )
    op.create_foreign_key(None, 'file_types', 'file_types', ['source_editing_file_type_id'], ['id'],
                            source_schema='event_paper_reviewing', referent_schema='event_editing')


def downgrade():
    op.drop_index('ix_uq_file_types_event_id_source_editing_file_type_id', table_name='file_types',
                  schema='event_paper_reviewing', postgresql_where=sa.text('source_editing_file_type_id IS NOT NULL'))
    op.drop_index('ix_uq_file_types_event_id_name_lower', table_name='file_types', schema='event_paper_reviewing')
    op.drop_index('ix_file_types_source_editing_file_type_id', table_name='file_types', schema='event_paper_reviewing')
    op.drop_column('file_types', 'source_editing_file_type_id', schema='event_paper_reviewing')
    op.create_index(
        'ix_uq_file_types_event_id_name_lower',
        'file_types',
        ['event_id', sa.text('lower(name)')],
        unique=True,
        schema='event_paper_reviewing'
    )
