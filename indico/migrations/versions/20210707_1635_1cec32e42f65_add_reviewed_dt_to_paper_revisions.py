"""Add reviewed_dt to paper revisions

Revision ID: 1cec32e42f65
Revises: cd3fef2095b4
Create Date: 2021-07-05 16:35:54.667174
"""
import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '1cec32e42f65'
down_revision = 'cd3fef2095b4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('revisions', sa.Column('reviewed_dt', UTCDateTime(), nullable=True), schema='event_editing')
    op.execute('UPDATE event_editing.revisions SET reviewed_dt = created_dt WHERE final_state != 0')
    op.create_check_constraint(
        'reviewed_dt_set_when_final_state',
        'revisions',
        '((final_state = 0) OR (reviewed_dt IS NOT NULL))',
        schema='event_editing'
    )


def downgrade():
    op.drop_constraint('ck_revisions_reviewed_dt_set_when_final_state', 'revisions', schema='event_editing')
    op.drop_column('revisions', 'reviewed_dt', schema='event_editing')
