"""Add abstract review tables

Revision ID: 4b33a3f6924f
Revises: 1eb296cc7b9e
Create Date: 2016-08-19 13:17:44.970756
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy import UTCDateTime
from indico.modules.events.abstracts.models.reviews import ReviewAction


# revision identifiers, used by Alembic.
revision = '4b33a3f6924f'
down_revision = '1eb296cc7b9e'


def upgrade():
    op.create_table(
        'abstract_review_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='event_abstracts'
    )

    op.create_table(
        'abstract_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('abstract_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('track_id', sa.Integer(), nullable=True, index=True),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.Column('modified_dt', UTCDateTime, nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('proposed_action', PyIntEnum(ReviewAction), nullable=False),
        sa.Column('proposed_track_id', sa.Integer(), nullable=True, index=True),
        sa.Column('proposed_contribution_type_id', sa.Integer(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['abstract_id'], ['event_abstracts.abstracts.id']),
        sa.ForeignKeyConstraint(['proposed_track_id'], ['events.tracks.id']),
        sa.ForeignKeyConstraint(['proposed_contribution_type_id'], ['events.contribution_types.id']),
        sa.ForeignKeyConstraint(['track_id'], ['events.tracks.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('abstract_id', 'user_id', 'track_id'),
        schema='event_abstracts'
    )

    op.create_table(
        'abstract_review_ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False, index=True),
        sa.Column('review_id', sa.Integer(), nullable=False, index=True),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['event_abstracts.abstract_review_questions.id']),
        sa.ForeignKeyConstraint(['review_id'], ['event_abstracts.abstract_reviews.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('review_id'),
        schema='event_abstracts'
    )


def downgrade():
    op.drop_table('abstract_review_ratings', schema='event_abstracts')
    op.drop_table('abstract_reviews', schema='event_abstracts')
    op.drop_table('abstract_review_questions', schema='event_abstracts')
