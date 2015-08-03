"""Add evaluation tables

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
        'evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('anonymous', sa.Boolean(), nullable=False),
        sa.Column('require_user', sa.Boolean(), nullable=False),
        sa.Column('start_dt', UTCDateTime, nullable=True),
        sa.Column('end_dt', UTCDateTime, nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_table(
        'evaluation_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False, index=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('help', sa.Text(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('field_type', sa.String(), nullable=False),
        sa.Column('field_data', postgresql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['events.evaluations.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_table(
        'evaluation_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),
        sa.Column('submitted_dt', UTCDateTime, nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['events.evaluations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.create_table(
        'evaluation_answers',
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('data', postgresql.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['events.evaluation_questions.id']),
        sa.ForeignKeyConstraint(['submission_id'], ['events.evaluation_submissions.id']),
        sa.PrimaryKeyConstraint('submission_id', 'question_id'),
        schema='events'
    )


def downgrade():
    op.drop_constraint('fk_evaluation_submissions_evaluation_id_evaluations', 'evaluation_submissions', schema='events')
    op.drop_constraint('fk_evaluation_questions_evaluation_id_evaluations', 'evaluation_questions', schema='events')
    op.drop_table('evaluations', schema='events')
    op.drop_table('evaluation_answers', schema='events')
    op.drop_table('evaluation_submissions', schema='events')
    op.drop_table('evaluation_questions', schema='events')
