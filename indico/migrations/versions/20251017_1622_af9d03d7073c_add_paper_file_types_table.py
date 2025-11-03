"""Add paper file types table

Revision ID: af9d03d7073c
Revises: 932389d22b1f
Create Date: 2025-10-14 13:38:27.605748
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'af9d03d7073c'
down_revision = '932389d22b1f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'file_types',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('extensions', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('allow_multiple_files', sa.Boolean(), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False),
        sa.Column('publishable', sa.Boolean(), nullable=False),
        sa.Column('filename_template', sa.String(), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
                                schema='event_paper_reviewing',
    )
    op.create_index('ix_uq_file_types_event_id_name_lower', 'file_types',
                    ['event_id', sa.text('lower(name)')], unique=True, schema='event_paper_reviewing')


def downgrade():
    op.drop_table('file_types', schema='event_paper_reviewing')
