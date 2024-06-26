"""Add constraints to ensure positive durations

Revision ID: 75db3a4a4ed4
Revises: 0f7c3b642036
Create Date: 2024-06-26 11:40:47.150327
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '75db3a4a4ed4'
down_revision = '0f7c3b642036'
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint('positive_default_contribution_duration', 'sessions', "default_contribution_duration > '0'",
                               schema='events')
    op.create_check_constraint('positive_duration', 'session_blocks', "duration > '0'",
                               schema='events')
    op.create_check_constraint('positive_duration', 'contributions', "duration > '0'",
                               schema='events')
    # Subcontributions and breaks are allowed to have a zero duration
    op.create_check_constraint('nonnegative_duration', 'breaks', "duration >= '0'",
                               schema='events')
    op.create_check_constraint('nonnegative_duration', 'subcontributions', "duration >= '0'",
                               schema='events')


def downgrade():
    op.drop_constraint('ck_sessions_positive_default_contribution_duration', 'sessions', schema='events')
    op.drop_constraint('ck_session_blocks_positive_duration', 'session_blocks', schema='events')
    op.drop_constraint('ck_contributions_positive_duration', 'contributions', schema='events')
    op.drop_constraint('ck_breaks_nonnegative_duration', 'breaks', schema='events')
    op.drop_constraint('ck_subcontributions_nonnegative_duration', 'subcontributions', schema='events')
