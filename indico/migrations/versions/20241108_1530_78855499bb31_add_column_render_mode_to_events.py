"""Add column render_mode to events.

Revision ID: 78855499bb31
Revises: 379ba72f4096
Create Date: 2024-07-22 18:37:15.333299
"""

from enum import Enum

import sqlalchemy as sa
from alembic import op

from indico.core.db.sqlalchemy import PyIntEnum


revision = '78855499bb31'
down_revision = '379ba72f4096'
branch_labels = None
depends_on = None


class _RenderMode(int, Enum):
    html = 1
    markdown = 2
    plain_text = 3


def upgrade():
    op.add_column('events', sa.Column('render_mode', PyIntEnum(_RenderMode), nullable=False,
                                      server_default='1'), schema='events')
    op.alter_column('events', 'render_mode', server_default=None, schema='events')


def downgrade():
    op.drop_column('events', 'render_mode', schema='events')
