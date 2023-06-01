"""Add data_export_requests table

Revision ID: e2b69fe5155d
Revises: 5d05eda06776
Create Date: 2023-05-08 15:37:24.134940
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.modules.users.models.export import DataExportOptions, DataExportRequestState


# revision identifiers, used by Alembic.
revision = 'e2b69fe5155d'
down_revision = '5d05eda06776'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'data_export_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requested_dt', UTCDateTime, nullable=False),
        sa.Column('selected_options', ARRAY(sa.Enum(DataExportOptions)), nullable=False),
        sa.Column('state', PyIntEnum(DataExportRequestState), nullable=False, server_default='0'),
        sa.Column('max_size_exceeded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('file_id', sa.Integer(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.ForeignKeyConstraint(['file_id'], ['indico.files.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.CheckConstraint(f'(state != {DataExportRequestState.success}) OR (file_id IS NOT NULL)',
                           name='success_has_file'),
        schema='users'
    )
    op.alter_column('data_export_requests', 'state', server_default=None, schema='users')


def downgrade():
    op.drop_table('data_export_requests', schema='users')
    # alembic does not automatically delete custom types
    # https://github.com/miguelgrinberg/Flask-Migrate/issues/48
    op.execute('DROP TYPE dataexportoptions')
