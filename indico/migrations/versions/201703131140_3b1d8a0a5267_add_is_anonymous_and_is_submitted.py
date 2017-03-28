"""Add is_anonymous and is_submitted columns to SurveySubmission

Revision ID: 3b1d8a0a5267
Revises: e185a5089262
Create Date: 2017-03-02 18:19:34.148361
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '3b1d8a0a5267'
down_revision = '2c87774642e7'


def upgrade():
    op.add_column('submissions',
                  sa.Column('is_anonymous', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_surveys')
    op.add_column('submissions',
                  sa.Column('is_submitted', sa.Boolean(), nullable=False, server_default='false'),
                  schema='event_surveys')
    op.execute('UPDATE event_surveys.submissions SET is_anonymous = (user_id IS NULL)')
    op.alter_column('submissions', 'is_anonymous', server_default=None, schema='event_surveys')
    op.execute('UPDATE event_surveys.submissions SET is_submitted = (submitted_dt IS NOT NULL)')
    op.alter_column('submissions', 'is_submitted', server_default=None, schema='event_surveys')
    op.alter_column('submissions', 'submitted_dt', nullable=True, schema='event_surveys')
    op.create_check_constraint('anonymous_or_user', 'submissions', 'is_anonymous OR user_id IS NOT NULL',
                               schema='event_surveys')
    op.create_check_constraint('dt_set_when_submitted', 'submissions',
                               'is_submitted = (submitted_dt IS NOT NULL)', schema='event_surveys')
    op.create_check_constraint('submitted_and_anonymous_no_user', 'submissions',
                               '(is_submitted AND is_anonymous) = (user_id IS NULL)', schema='event_surveys')


def downgrade():
    op.drop_constraint('ck_submissions_anonymous_or_user', 'submissions', schema='event_surveys')
    op.drop_constraint('ck_submissions_dt_set_when_submitted', 'submissions', schema='event_surveys')
    op.drop_constraint('ck_submissions_submitted_and_anonymous_no_user', 'submissions', schema='event_surveys')
    op.drop_column('submissions', 'is_anonymous', schema='event_surveys')
    op.drop_column('submissions', 'is_submitted', schema='event_surveys')
    op.alter_column('submissions', 'submitted_dt', nullable=False, schema='event_surveys')
