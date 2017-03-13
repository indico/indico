"""Delete legacy paper tables

Revision ID: fb7b6aa148e
Revises: 25d478c9d690
Create Date: 2017-02-22 14:43:34.952274
"""

import sqlalchemy as sa
from alembic import context, op
from indico.core.db.sqlalchemy import UTCDateTime, PyIntEnum
from indico.util.struct.enum import RichIntEnum


# revision identifiers, used by Alembic.
revision = 'fb7b6aa148e'
down_revision = '25d478c9d690'


class PaperReviewingRoleType(RichIntEnum):
    reviewer = 0
    referee = 1
    editor = 2


def upgrade():
    if not context.is_offline_mode():
        # sanity check to avoid running w/o papers migrated
        conn = op.get_bind()
        has_new_papers = conn.execute("SELECT EXISTS (SELECT 1 FROM event_paper_reviewing.legacy_paper_files)").scalar()
        has_old_papers = conn.execute("SELECT EXISTS (SELECT 1 FROM event_paper_reviewing.revisions)").scalar()
        if has_old_papers and not has_new_papers:
            raise Exception('Upgrade to {} and run the event_papers zodb import first!'.format(down_revision))

    op.drop_table('legacy_paper_files', schema='event_paper_reviewing')
    op.drop_table('legacy_contribution_roles', schema='event_paper_reviewing')


def downgrade():
    op.create_table(
        'legacy_contribution_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('role', PyIntEnum(PaperReviewingRoleType), nullable=False, index=True),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_paper_reviewing'
    )

    op.create_table(
        'legacy_paper_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contribution_id', sa.Integer(), nullable=False, index=True),
        sa.Column('revision_id', sa.Integer(), nullable=True),
        sa.Column('storage_backend', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('storage_file_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.ForeignKeyConstraint(['contribution_id'], ['events.contributions.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_paper_reviewing'
    )
