"""Added event-level stylesheet storage

Revision ID: 35e20fe25c8f
Revises: 2fd1bc34a83c
Create Date: 2015-08-14 13:19:09.311973
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '35e20fe25c8f'
down_revision = '2fd1bc34a83c'


def upgrade():
    op.create_table('css_files',
                    sa.Column('created_dt', UTCDateTime, nullable=False),
                    sa.Column('filename', sa.String(), nullable=False),
                    sa.Column('content_type', sa.String(), nullable=False),
                    sa.Column('size', sa.BigInteger(), nullable=False),
                    sa.Column('storage_backend', sa.String(), nullable=False),
                    sa.Column('storage_file_id', sa.String(), nullable=False),
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False, unique=True, index=True),
                    sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
                    sa.PrimaryKeyConstraint('id'),
                    schema='events')


def downgrade():
    op.drop_table('css_files', schema='events')
