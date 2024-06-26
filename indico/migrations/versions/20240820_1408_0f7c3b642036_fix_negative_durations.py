"""Set negative and zero-duration entries to a positive value

Revision ID: 0f7c3b642036
Revises: 5fa92194c124
Create Date: 2024-06-26 11:01:00.506858
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '0f7c3b642036'
down_revision = '5fa92194c124'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE events.sessions SET default_contribution_duration = '1 minute' WHERE default_contribution_duration <= '0'")
    op.execute("UPDATE events.session_blocks SET duration = '1 minute' WHERE duration < '0'")
    op.execute("UPDATE events.contributions SET duration = '1 minute' WHERE duration < '0'")
    op.execute("UPDATE events.breaks SET duration = '1 minute' WHERE duration < '0'")
    op.execute("UPDATE events.subcontributions SET duration = '0' WHERE duration < '0'")

    # After reseting the durations to a positive value, it is possible that some entries
    # end after the parent block which must be fixed by extending the block duration.
    entry_ends_after_parent = '''
        FROM events.timetable_entries te
        JOIN events.timetable_entries tep ON (tep.id = te.parent_id)
        LEFT JOIN events.contributions c ON (c.id = te.contribution_id)
        LEFT JOIN events.breaks b ON (b.id = te.break_id)
        WHERE bl.id = tep.session_block_id AND te.parent_id IS NOT NULL AND te.type IN (2, 3) AND
            (te.start_dt + COALESCE(c.duration, b.duration)) > (tep.start_dt + bl.duration)'''

    op.execute(f'''
        UPDATE events.session_blocks bl SET duration =
            (SELECT MAX(te.start_dt + COALESCE(c.duration, b.duration) - tep.start_dt)
             {entry_ends_after_parent})
        {entry_ends_after_parent}''')  # noqa: S608


def downgrade():
    pass
