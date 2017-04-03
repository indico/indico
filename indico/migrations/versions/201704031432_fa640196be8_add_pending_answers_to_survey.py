"""Add pending_answers to survey submissions

Revision ID: fa640196be8
Revises: 3b1d8a0a5267
Create Date: 2017-03-08 16:17:16.545705
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'fa640196be8'
down_revision = '3b1d8a0a5267'


def upgrade():
    op.add_column('submissions',
                  sa.Column('pending_answers', postgresql.JSON(), server_default='{}'),
                  schema='event_surveys')
    op.alter_column('submissions', 'pending_answers', server_default=None, schema='event_surveys')


def downgrade():
    op.drop_column('submissions', 'pending_answers', schema='event_surveys')
