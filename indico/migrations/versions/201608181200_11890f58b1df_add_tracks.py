"""Add tracks

Revision ID: 11890f58b1df
Revises: 4d4b95748173
Create Date: 2016-08-16 16:48:27.441514
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '11890f58b1df'
down_revision = '15661b6cd066'


def upgrade():
    op.create_table(
        'tracks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )


def downgrade():
    op.drop_table('tracks', schema='events')
