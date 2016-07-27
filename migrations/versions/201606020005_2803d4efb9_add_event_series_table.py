"""Add event series table

Revision ID: 2803d4efb9
Revises: 35eac9fee166
Create Date: 2016-07-25 08:55:25.652408
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '2803d4efb9'
down_revision = '35eac9fee166'


def upgrade():
    op.create_table(
        'series',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('show_sequence_in_title', sa.Boolean(), nullable=False),
        sa.Column('show_links', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
    op.add_column('events', sa.Column('series_id', sa.Integer(), nullable=True), schema='events')
    op.create_index(None, 'events', ['series_id'], schema='events')
    op.create_foreign_key(None,
                          'events', 'series',
                          ['series_id'], ['id'],
                          source_schema='events', referent_schema='events')


def downgrade():
    op.drop_column('events', 'series_id', schema='events')
    op.drop_table('series', schema='events')
