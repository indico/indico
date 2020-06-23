"""Add metadata to event logs

Revision ID: 05f227f4b938
Revises: c0fc1e46888b
Create Date: 2020-06-23 17:18:05.171784
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '05f227f4b938'
down_revision = 'b6dd0a4ed40d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('logs', sa.Column('meta', postgresql.JSONB(), nullable=False, server_default='{}'),
                  schema='events')
    op.alter_column('logs', 'meta', server_default=None, schema='events')
    op.create_index(None, 'logs', ['meta'], unique=False, schema='events', postgresql_using='gin')


def downgrade():
    op.drop_column('logs', 'meta', schema='events')
