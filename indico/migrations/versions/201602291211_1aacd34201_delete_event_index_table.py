"""Delete event_index table

Revision ID: 1aacd34201
Revises: 291a596186cb
Create Date: 2016-02-29 12:11:20.976101
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg


# revision identifiers, used by Alembic.
revision = '1aacd34201'
down_revision = '291a596186cb'


def upgrade():
    op.drop_table('event_index', schema='events')


def downgrade():
    op.create_table(
        'event_index',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('title_vector', pg.TSVECTOR(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False, index=True),
        sa.Column('end_date', sa.DateTime(), nullable=False, index=True),
        sa.Index(None, 'title_vector', postgresql_using='gin'),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )
