"""Add survey tables

Revision ID: 3fcf833adc2d
Revises: 3778dc365e54
Create Date: 2015-07-27 11:14:06.639780
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '3fcf833adc2d'
down_revision = '3778dc365e54'


def upgrade():
    op.create_table(
        'surveys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('introduction', sa.Text(), nullable=False),
        sa.Column('anonymous', sa.Boolean(), nullable=False),
        sa.Column('require_user', sa.Boolean(), nullable=False),
        sa.Column('submission_limit', sa.Integer(), nullable=True),
        sa.Column('start_dt', UTCDateTime, nullable=True),
        sa.Column('end_dt', UTCDateTime, nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('start_notification_sent', sa.Boolean(), nullable=False),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=False),
        sa.Column('notify_participants', sa.Boolean(), nullable=False),
        sa.Column('start_notification_emails', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('new_submission_emails', postgresql.ARRAY(sa.String()), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_table(
        'survey_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('survey_id', sa.Integer(), nullable=False, index=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('field_type', sa.String(), nullable=False),
        sa.Column('field_data', postgresql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['survey_id'], ['events.surveys.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_table(
        'survey_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('survey_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('submitted_dt', UTCDateTime, nullable=False),
        sa.ForeignKeyConstraint(['survey_id'], ['events.surveys.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_table(
        'survey_answers',
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('data', postgresql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['events.survey_questions.id']),
        sa.ForeignKeyConstraint(['submission_id'], ['events.survey_submissions.id']),
        sa.PrimaryKeyConstraint('submission_id', 'question_id'),
        schema='events'
    )


def downgrade():
    op.drop_constraint('fk_survey_submissions_survey_id_surveys', 'survey_submissions', schema='events')
    op.drop_constraint('fk_survey_questions_survey_id_surveys', 'survey_questions', schema='events')
    op.drop_table('surveys', schema='events')
    op.drop_table('survey_answers', schema='events')
    op.drop_table('survey_submissions', schema='events')
    op.drop_table('survey_questions', schema='events')
