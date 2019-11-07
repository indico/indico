"""Add files table

Revision ID: bb522e9f9066
Revises: a2472148d2c5
Create Date: 2019-11-07 18:16:27.097230
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = 'bb522e9f9066'
down_revision = 'a2472148d2c5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(), nullable=False, index=True, unique=True),
        sa.Column('claimed', sa.Boolean(), nullable=False),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('storage_backend', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('md5', sa.String(), nullable=False),
        sa.Column('storage_file_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='indico'
    )


def downgrade():
    op.drop_table('files', schema='indico')
