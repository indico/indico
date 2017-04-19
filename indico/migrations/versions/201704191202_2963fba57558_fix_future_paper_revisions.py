"""Fix future paper revisions

Revision ID: 2963fba57558
Revises: 098311458f37
Create Date: 2017-04-19 12:02:16.187401
"""

from collections import Counter
from datetime import timedelta

from alembic import context, op

# revision identifiers, used by Alembic.
revision = '2963fba57558'
down_revision = '098311458f37'
branch_labels = None
depends_on = None


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()

    conn.execute('''
        UPDATE event_paper_reviewing.revisions
        SET submitted_dt = judgment_dt
        WHERE judgment_dt < submitted_dt;

        UPDATE event_paper_reviewing.revisions
        SET submitted_dt = now()
        WHERE submitted_dt > now();
    ''')

    res = conn.execute("""
        SELECT contribution_id
        FROM event_paper_reviewing.revisions r
        JOIN events.contributions c ON (c.id = r.contribution_id)
        GROUP BY contribution_id, submitted_dt
        HAVING COUNT(*) > 1;
    """)
    ids = {x.contribution_id for x in res}
    stmt = """
        SELECT id, submitted_dt
        FROM event_paper_reviewing.revisions
        WHERE contribution_id = %s
        ORDER BY submitted_dt ASC, id ASC
    """
    for contrib_id in ids:
        res = conn.execute(stmt, (contrib_id,))
        times = Counter()
        for row in res:
            if times[row.submitted_dt] > 0:
                dt = row.submitted_dt + timedelta(seconds=times[row.submitted_dt])
                conn.execute("UPDATE event_paper_reviewing.revisions SET submitted_dt = %s WHERE id = %s", (dt, row.id))
            times[row.submitted_dt] += 1

    conn.execute('''
        UPDATE event_paper_reviewing.revisions
        SET submitted_dt = judgment_dt
        WHERE judgment_dt < submitted_dt;
    ''')


def downgrade():
    pass
