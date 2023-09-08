"""Add data_export_requests table

Revision ID: e2b69fe5155d
Revises: 0c44046dc1be
Create Date: 2023-05-08 15:37:24.134940
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime


class _DataExportRequestState(int, Enum):
    none = 0
    running = 1
    success = 2
    failed = 3
    expired = 4


class _DataExportOptions(int, Enum):
    personal_data = 1
    settings = 2
    contribs = 3
    registrations = 4
    room_booking = 5
    abstracts_papers = 6
    survey_submissions = 7
    attachments = 8
    editables = 9
    misc = 10


# revision identifiers, used by Alembic.
revision = 'e2b69fe5155d'
down_revision = '0c44046dc1be'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'data_export_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requested_dt', UTCDateTime, nullable=False),
        sa.Column('selected_options', ARRAY(sa.Enum(_DataExportOptions, native_enum=False)), nullable=False),
        sa.Column('state', PyIntEnum(_DataExportRequestState), nullable=False),
        sa.Column('max_size_exceeded', sa.Boolean(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('file_id', sa.Integer(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['file_id'], ['indico.files.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.CheckConstraint(f'(state != {_DataExportRequestState.success}) OR (file_id IS NOT NULL)',
                           name='success_has_file'),
        schema='users'
    )
    op.alter_column('data_export_requests', 'state', server_default=None, schema='users')


def downgrade():
    op.drop_table('data_export_requests', schema='users')
