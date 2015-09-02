"""Add survey tables

Revision ID: 3fcf833adc2d
Revises: 2fd1bc34a83c
Create Date: 2015-07-27 11:14:06.639780
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.ddl import CreateSchema, DropSchema

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.modules.events.surveys.models.items import SurveyItemType

# revision identifiers, used by Alembic.
revision = '3fcf833adc2d'
down_revision = '2fd1bc34a83c'


def upgrade():
    op.execute(CreateSchema('event_surveys'))
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
        sa.CheckConstraint('anonymous OR require_user', name='valid_anonymous_user'),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_surveys'
    )
    op.create_table(
        'items',
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
        sa.Column('display_as_section', sa.Boolean(), nullable=True),
        sa.CheckConstraint("type != 1 OR (title IS NOT NULL AND is_required IS NOT NULL AND field_type IS NOT NULL AND "
                           "parent_id IS NOT NULL AND display_as_section IS NULL)",
                           name='valid_question'),
        sa.CheckConstraint("type != 2 OR (title IS NOT NULL AND is_required IS NULL AND field_type IS NULL AND "
                           "field_data::text = '{}' AND parent_id IS NULL AND display_as_section IS NOT NULL)",
                           name='valid_section'),
        sa.CheckConstraint("type != 3 OR (title IS NULL AND is_required IS NULL AND field_type IS NULL "
                           "AND field_data::text = '{}' AND parent_id IS NOT NULL AND display_as_section IS NULL)",
                           name='valid_text'),
        sa.ForeignKeyConstraint(['survey_id'], ['event_surveys.surveys.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['event_surveys.items.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_surveys'
    )
    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('survey_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('submitted_dt', UTCDateTime, nullable=False),
        sa.ForeignKeyConstraint(['survey_id'], ['event_surveys.surveys.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_surveys'
    )
    op.create_table(
        'answers',
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('data', postgresql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['event_surveys.items.id']),
        sa.ForeignKeyConstraint(['submission_id'], ['event_surveys.submissions.id']),
        sa.PrimaryKeyConstraint('submission_id', 'question_id'),
        schema='event_surveys'
    )


def downgrade():
    op.drop_table('answers', schema='event_surveys')
    op.drop_table('submissions', schema='event_surveys')
    op.drop_table('items', schema='event_surveys')
    op.drop_table('surveys', schema='event_surveys')
    op.execute(DropSchema('event_surveys'))
