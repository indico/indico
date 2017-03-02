"""Delete legacy abstract tables

Revision ID: 3bbcba10f5b1
Revises: 2f57a1a87b83
Create Date: 2016-11-16 15:09:01.296571
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '3bbcba10f5b1'
down_revision = '2f57a1a87b83'


def upgrade():
    op.drop_table('judgments', schema='event_abstracts')
    op.drop_table('legacy_abstracts', schema='event_abstracts')


def downgrade():
    op.create_table(
        'legacy_abstracts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('friendly_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('description', sa.TEXT(), nullable=False),
        sa.Column('accepted_track_id', sa.Integer(), nullable=True, index=True),
        sa.Column('accepted_type_id', sa.Integer(), nullable=True, index=True),
        sa.Column('type_id', sa.Integer(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['accepted_type_id'], ['events.contribution_types.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.ForeignKeyConstraint(['type_id'], ['events.contribution_types.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('friendly_id', 'event_id'),
        schema='event_abstracts'
    )
    op.create_table(
        'judgments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('creation_dt', postgresql.TIMESTAMP(), nullable=False, index=True),
        sa.Column('abstract_id', sa.Integer(), nullable=False, index=True),
        sa.Column('track_id', sa.Integer(), nullable=False),
        sa.Column('judge_user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('accepted_type_id', sa.Integer(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['accepted_type_id'], ['events.contribution_types.id']),
        sa.ForeignKeyConstraint(['judge_user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('abstract_id', 'track_id', 'judge_user_id'),
        schema='event_abstracts'
    )
