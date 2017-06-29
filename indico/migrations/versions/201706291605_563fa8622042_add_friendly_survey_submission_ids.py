"""Add friendly survey submission ids

Revision ID: 563fa8622042
Revises: 35d76c40ca48
Create Date: 2017-06-29 16:05:49.284702
"""
from itertools import groupby
from operator import attrgetter

import sqlalchemy as sa
from alembic import op, context


# revision identifiers, used by Alembic.
revision = '563fa8622042'
down_revision = '35d76c40ca48'
branch_labels = None
depends_on = None


def _set_friendly_ids(conn):
    res = conn.execute('''
        SELECT id, survey_id
        FROM event_surveys.submissions
        ORDER BY survey_id, submitted_dt, id
    ''')
    for survey_id, rows in groupby(res, key=attrgetter('survey_id')):
        submission_ids = [x.id for x in rows]
        for i, submission_id in enumerate(submission_ids, 1):
            conn.execute('UPDATE event_surveys.submissions SET friendly_id = %s WHERE id = %s', (i, submission_id))
        conn.execute('UPDATE event_surveys.surveys SET last_friendly_submission_id = %s WHERE id = %s', (i, survey_id))


def upgrade():
    if context.is_offline_mode():
        raise Exception('This upgrade is only possible in online mode')
    conn = op.get_bind()
    op.add_column('surveys', sa.Column('last_friendly_submission_id', sa.Integer(), nullable=False, server_default='0'),
                  schema='event_surveys')
    op.alter_column('surveys', 'last_friendly_submission_id', server_default=None, schema='event_surveys')
    op.add_column('submissions', sa.Column('friendly_id', sa.Integer(), nullable=True), schema='event_surveys')
    _set_friendly_ids(conn)
    op.alter_column('submissions', 'friendly_id', nullable=False, schema='event_surveys')


def downgrade():
    op.drop_column('surveys', 'last_friendly_submission_id', schema='event_surveys')
    op.drop_column('submissions', 'friendly_id', schema='event_surveys')
