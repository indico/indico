"""Add news table

Revision ID: 179817f1fb97
Revises: 2803d4efb9
Create Date: 2016-07-01 14:22:07.053308
"""

import sqlalchemy as sa
from alembic import op
from indico.core.db.sqlalchemy import UTCDateTime


# revision identifiers, used by Alembic.
revision = '179817f1fb97'
down_revision = '2803d4efb9'


def upgrade():
    op.create_table(
        'news',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_dt', UTCDateTime, nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='indico'
    )


def downgrade():
    op.drop_table('news', schema='indico')
