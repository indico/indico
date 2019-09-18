"""Add track_groups table

Revision ID: eefba82b42c5
Revises: 620b312814f3
Create Date: 2019-07-31 15:15:48.350924
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'eefba82b42c5'
down_revision = '620b312814f3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'track_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        schema='events'
    )
    op.add_column('tracks', sa.Column('track_group_id', sa.Integer(), nullable=True, index=True), schema='events')
    op.create_foreign_key(None, 'tracks', 'track_groups', ['track_group_id'], ['id'], source_schema='events',
                          referent_schema='events', ondelete='SET NULL')


def downgrade():
    op.drop_column('tracks', 'track_group_id', schema='events')
    op.drop_table('track_groups', schema='events')
