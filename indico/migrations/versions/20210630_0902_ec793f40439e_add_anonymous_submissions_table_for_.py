"""Add anonymous_submissions table for surveys

Revision ID: ec793f40439e
Revises: 90384b9b3d22
Create Date: 2021-06-30 09:02:33.328010
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'ec793f40439e'
down_revision = '90384b9b3d22'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'anonymous_submissions',
        sa.Column('survey_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['survey_id'], ['event_surveys.surveys.id'],
                                name=op.f('fk_anonymous_submissions_survey_id_surveys')),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id'], name=op.f('fk_anonymous_submissions_user_id_users')),
        sa.PrimaryKeyConstraint('survey_id', 'user_id', name=op.f('pk_anonymous_submissions')),
        schema='event_surveys'
    )
    op.create_index(op.f('ix_anonymous_submissions_survey_id'), 'anonymous_submissions', ['survey_id'], unique=False,
                    schema='event_surveys')
    op.create_index(op.f('ix_anonymous_submissions_user_id'), 'anonymous_submissions', ['user_id'], unique=False,
                    schema='event_surveys')


def downgrade():
    op.drop_index(op.f('ix_anonymous_submissions_user_id'), table_name='anonymous_submissions', schema='event_surveys')
    op.drop_index(op.f('ix_anonymous_submissions_survey_id'), table_name='anonymous_submissions', schema='event_surveys')
    op.drop_table('anonymous_submissions', schema='event_surveys')
