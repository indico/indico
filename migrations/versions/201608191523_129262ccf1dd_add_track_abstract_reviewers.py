"""Add track abstract reviewers

Revision ID: 129262ccf1dd
Revises: 4b33a3f6924f
Create Date: 2016-08-19 15:23:29.798327
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '129262ccf1dd'
down_revision = '4b33a3f6924f'


def upgrade():
    op.create_table(
        'track_abstract_reviewers',
        sa.Column('user_id', sa.Integer(), nullable=False, autoincrement=False, index=True),
        sa.Column('track_id', sa.Integer(), nullable=False, autoincrement=False, index=True),
        sa.ForeignKeyConstraint(['track_id'], ['events.tracks.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.users.id']),
        sa.PrimaryKeyConstraint('user_id', 'track_id'),
        schema='events'
    )


def downgrade():
    op.drop_table('track_abstract_reviewers', schema='events')
