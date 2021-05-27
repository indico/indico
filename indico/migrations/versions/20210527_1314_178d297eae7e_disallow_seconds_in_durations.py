"""Disallow seconds in durations

Revision ID: 178d297eae7e
Revises: cf9e1b4e2f5f
Create Date: 2021-05-27 13:14:59.253773
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '178d297eae7e'
down_revision = 'cf9e1b4e2f5f'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        UPDATE events.contributions SET duration = date_trunc('minute', duration) WHERE date_trunc('minute', duration) != duration;
        UPDATE events.subcontributions SET duration = date_trunc('minute', duration) WHERE date_trunc('minute', duration) != duration;
        UPDATE events.breaks SET duration = date_trunc('minute', duration) WHERE date_trunc('minute', duration) != duration;
        UPDATE events.session_blocks SET duration = date_trunc('minute', duration) WHERE date_trunc('minute', duration) != duration;
        UPDATE events.sessions SET default_contribution_duration = date_trunc('minute', default_contribution_duration) WHERE date_trunc('minute', default_contribution_duration) != default_contribution_duration;
    ''')

    # force execution of trigger events
    op.execute('SET CONSTRAINTS ALL IMMEDIATE')

    op.create_check_constraint(
        'duration_no_seconds',
        'breaks',
        "date_trunc('minute', duration) = duration",
        schema='events'
    )
    op.create_check_constraint(
        'duration_no_seconds',
        'contributions',
        "date_trunc('minute', duration) = duration",
        schema='events'
    )
    op.create_check_constraint(
        'duration_no_seconds',
        'session_blocks',
        "date_trunc('minute', duration) = duration",
        schema='events'
    )
    op.create_check_constraint(
        'duration_no_seconds',
        'subcontributions',
        "date_trunc('minute', duration) = duration",
        schema='events'
    )
    op.create_check_constraint(
        'default_contribution_duration_no_seconds',
        'sessions',
        "date_trunc('minute', default_contribution_duration) = default_contribution_duration",
        schema='events'
    )


def downgrade():
    op.drop_constraint('ck_breaks_duration_no_seconds', 'breaks', schema='events')
    op.drop_constraint('ck_contributions_duration_no_seconds', 'contributions', schema='events')
    op.drop_constraint('ck_session_blocks_duration_no_seconds', 'session_blocks', schema='events')
    op.drop_constraint('ck_subcontributions_duration_no_seconds', 'subcontributions', schema='events')
    op.drop_constraint('ck_sessions_default_contribution_duration_no_seconds', 'sessions', schema='events')
