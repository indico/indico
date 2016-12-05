"""Add paper tables

Revision ID: 2287c5d5680c
Revises: 1e94b3cf3cfd
Create Date: 2016-12-05 17:44:40.392524
"""

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import UTCDateTime, PyIntEnum
from indico.modules.events.papers.models.revisions import PaperRevisionState


# revision identifiers, used by Alembic.
revision = '2287c5d5680c'
down_revision = '1e94b3cf3cfd'


def upgrade():
    op.create_table(
        'revisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('submitter_id', sa.Integer(), nullable=False, index=True),
        sa.Column('submitted_dt', UTCDateTime, nullable=False),
        sa.Column('state', PyIntEnum(PaperRevisionState), nullable=False),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.ForeignKeyConstraint(['submitter_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.Index(None, 'contribution_id', unique=True, postgresql_where=sa.text('state = 2')),
        schema='event_paper_reviewing'
    )
    op.create_table(
        'files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('revision_id', sa.Integer(), nullable=True, index=True),
        sa.Column('storage_backend', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('storage_file_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.ForeignKeyConstraint(['revision_id'], ['event_paper_reviewing.revisions.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_paper_reviewing'
    )


def downgrade():
    op.drop_table('files', schema='event_paper_reviewing')
    op.drop_table('revisions', schema='event_paper_reviewing')
