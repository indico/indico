"""Add event keywords column

Revision ID: 85637555724
Revises: 179817f1fb97
Create Date: 2016-07-27 09:55:20.028318
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg


# revision identifiers, used by Alembic.
revision = '85637555724'
down_revision = '179817f1fb97'


def upgrade():
    op.add_column('events', sa.Column('keywords', pg.ARRAY(sa.String()), nullable=False, server_default='{}'),
                  schema='events')
    op.alter_column('events', 'keywords', server_default=None, schema='events')


def downgrade():
    op.drop_column('events', 'keywords', schema='events')
