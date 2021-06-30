"""Add anonymous_submissions table for surveys

Revision ID: 356b8985ae7c
Revises: 90384b9b3d22
Create Date: 2021-06-30 11:04:32.349228
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '356b8985ae7c'
down_revision = '90384b9b3d22'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'anonymous_submissions',
        sa.Column('survey_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['survey_id'], ['event_surveys.surveys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('survey_id', 'user_id'),
        schema='event_surveys'
    )


def downgrade():
    op.drop_table('anonymous_submissions', schema='event_surveys')
