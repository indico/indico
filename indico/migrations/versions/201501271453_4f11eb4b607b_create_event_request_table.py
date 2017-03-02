"""Create event request table

Revision ID: 4f11eb4b607b
Revises: 50c2b5ee2726
Create Date: 2015-01-27 14:53:31.162822
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.modules.events.requests.models.requests import RequestState


# revision identifiers, used by Alembic.
revision = '4f11eb4b607b'
down_revision = '50c2b5ee2726'


def upgrade():
    op.create_table('requests',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False, index=True),
                    sa.Column('type', sa.String(), nullable=False),
                    sa.Column('state', PyIntEnum(RequestState), nullable=False),
                    sa.Column('data', postgresql.JSON(), nullable=False),
                    sa.Column('created_by_id', sa.Integer(), nullable=False),
                    sa.Column('created_dt', UTCDateTime, nullable=False, index=True),
                    sa.Column('processed_by_id', sa.Integer(), nullable=True),
                    sa.Column('processed_dt', UTCDateTime, nullable=True),
                    sa.Column('comment', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    schema='events')


def downgrade():
    op.drop_table('requests', schema='events')
