"""Add report_links table

Revision ID: 3e7a0c029abb
Revises: ce6c3f7f35e
Create Date: 2016-02-12 13:44:26.447430
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '3e7a0c029abb'
down_revision = 'ce6c3f7f35e'


def upgrade():
    op.create_table(
        'report_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('uuid', pg.UUID(), nullable=False, index=True, unique=True),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.Column('last_used_dt', UTCDateTime, nullable=True),
        sa.Column('data', pg.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.events.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='events'
    )


def downgrade():
    op.drop_table('report_links', schema='events')
