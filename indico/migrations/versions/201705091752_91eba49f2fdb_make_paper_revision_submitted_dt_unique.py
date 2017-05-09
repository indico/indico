"""Make paper revision submitted_dt unique

Revision ID: 91eba49f2fdb
Revises: 0253155a2219
Create Date: 2017-05-09 17:52:01.867994
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '91eba49f2fdb'
down_revision = '0253155a2219'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(None, 'revisions', ['contribution_id', 'submitted_dt'], schema='event_paper_reviewing')


def downgrade():
    op.drop_constraint('uq_revisions_contribution_id_submitted_dt', 'revisions', schema='event_paper_reviewing')
