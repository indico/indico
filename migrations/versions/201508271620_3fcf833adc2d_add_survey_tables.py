"""Add survey tables

Revision ID: 3fcf833adc2d
Revises: 2fd1bc34a83c
Create Date: 2015-07-27 11:14:06.639780
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.modules.events.surveys.models.items import SurveyItemType

# revision identifiers, used by Alembic.
revision = '3fcf833adc2d'
down_revision = '2fd1bc34a83c'


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
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_table(
        'survey_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('survey_id', sa.Integer(), nullable=False, index=True),
        sa.Column('parent_id', sa.Integer(), nullable=True, index=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('type', PyIntEnum(SurveyItemType), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.Column('field_type', sa.String(), nullable=True),
        sa.Column('field_data', postgresql.JSON(), nullable=False),
        sa.CheckConstraint("type != 1 OR (title IS NOT NULL AND is_required IS NOT NULL AND field_type IS NOT NULL AND "
                           "parent_id IS NOT NULL)",
                           name='valid_question'),
        sa.CheckConstraint("type != 2 OR (title IS NOT NULL AND is_required IS NULL AND field_type IS NULL AND "
                           "field_data::text = '{}' AND parent_id IS NULL)",
                           name='valid_section'),
        sa.CheckConstraint("type != 3 OR (title IS NULL AND is_required IS NULL AND field_type IS NULL "
                           "AND field_data::text = '{}')",
                           name='valid_text'),
        sa.ForeignKeyConstraint(['survey_id'], ['events.surveys.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['events.survey_items.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_table(
        'survey_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('survey_id', sa.Integer(), nullable=False, index=True),
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
        sa.ForeignKeyConstraint(['question_id'], ['events.survey_items.id']),
        sa.ForeignKeyConstraint(['submission_id'], ['events.survey_submissions.id']),
        sa.PrimaryKeyConstraint('submission_id', 'question_id'),
        schema='events'
    )


def downgrade():
    op.drop_constraint('fk_survey_submissions_survey_id_surveys', 'survey_submissions', schema='events')
    op.drop_constraint('fk_survey_items_survey_id_surveys', 'survey_items', schema='events')
    op.drop_table('surveys', schema='events')
    op.drop_table('survey_answers', schema='events')
    op.drop_table('survey_submissions', schema='events')
    op.drop_table('survey_items', schema='events')
